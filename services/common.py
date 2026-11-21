"""Общий код для микросервисов: БД, CRUD-маршруты, HTTP-вызовы между сервисами."""
import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

from flask import jsonify, request

UNIQUE_MSG = "Запись с таким уникальным значением уже существует."
FK_MSG = "Выбранная связанная запись не существует."
CHECK_MSG = "Проверьте корректность дат и числовых значений."
OTHER_MSG = "Не удалось сохранить запись. Проверьте введённые данные."
IN_USE_MSG = "Нельзя удалить запись: она используется в связанных данных."


class ServiceError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def call(method, url, payload=None, timeout=5):
    """HTTP-вызов другого сервиса. Возвращает (status, json)."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return resp.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as exc:
        body = exc.read()
        try:
            parsed = json.loads(body)
        except ValueError:
            parsed = {"error": body.decode("utf-8", "replace")}
        return exc.code, parsed
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ServiceError(503, f"Сервис недоступен: {url}") from exc


def make_get_db(app):
    def get_db():
        db_path = Path(app.config["DATABASE"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    return get_db


def register_common(app, get_db, schema, service_name):
    """Health-check, обработка ошибок, инициализация БД."""
    @app.get("/health")
    def health():
        return jsonify(service=service_name, status="ok")

    @app.errorhandler(ServiceError)
    def service_error(exc):
        return jsonify(error=exc.message), exc.status

    def init_db():
        with get_db() as conn:
            conn.executescript(schema)

    with app.app_context():
        init_db()
    return init_db


def register_crud(app, get_db, *, entity, table, fields, search, list_sql,
                  before_save=None, before_delete=None, enrich=None):
    """Регистрирует /api/<entity> (список, чтение, создание, изменение, удаление)."""

    def rows_to_list(rows):
        data = [dict(r) for r in rows]
        return enrich(data) if enrich else data

    @app.get(f"/api/{entity}", endpoint=f"{entity}_list")
    def list_records():
        q = request.args.get("q", "")
        sql = list_sql
        params = []
        if q.strip():
            clauses = [f"CAST({f} AS TEXT) LIKE ?" for f in search]
            sql += " WHERE " + " OR ".join(clauses)
            params = [f"%{q.strip()}%"] * len(clauses)
        sql += " ORDER BY id DESC"
        with get_db() as conn:
            rows = conn.execute(sql, params).fetchall()
        return jsonify(rows_to_list(rows))

    @app.get(f"/api/{entity}/<int:record_id>", endpoint=f"{entity}_get")
    def get_record(record_id):
        with get_db() as conn:
            row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (record_id,)).fetchone()
        if row is None:
            return jsonify(error="Не найдено"), 404
        return jsonify(dict(row))

    def save(values, record_id=None):
        values = {k: v for k, v in (values or {}).items() if k in fields}
        if before_save:
            try:
                before_save(values)
            except ValueError as exc:
                return jsonify(error=str(exc)), 400
        names = list(values.keys())
        try:
            with get_db() as conn:
                if record_id is None:
                    ph = ", ".join("?" for _ in names)
                    cur = conn.execute(f"INSERT INTO {table} ({', '.join(names)}) VALUES ({ph})",
                                       [values[n] for n in names])
                    new_id = cur.lastrowid
                else:
                    assign = ", ".join(f"{n}=?" for n in names)
                    conn.execute(f"UPDATE {table} SET {assign} WHERE id=?",
                                 [values[n] for n in names] + [record_id])
                    new_id = record_id
        except sqlite3.IntegrityError as exc:
            message = str(exc)
            if "UNIQUE" in message:
                return jsonify(error=UNIQUE_MSG), 400
            if "FOREIGN KEY" in message:
                return jsonify(error=FK_MSG), 400
            if "CHECK constraint" in message:
                return jsonify(error=CHECK_MSG), 400
            return jsonify(error=OTHER_MSG), 400
        return jsonify(id=new_id), (201 if record_id is None else 200)

    @app.post(f"/api/{entity}", endpoint=f"{entity}_create")
    def create_record():
        return save(request.get_json(silent=True))

    @app.put(f"/api/{entity}/<int:record_id>", endpoint=f"{entity}_update")
    def update_record(record_id):
        with get_db() as conn:
            exists = conn.execute(f"SELECT 1 FROM {table} WHERE id=?", (record_id,)).fetchone()
        if not exists:
            return jsonify(error="Не найдено"), 404
        return save(request.get_json(silent=True), record_id)

    @app.delete(f"/api/{entity}/<int:record_id>", endpoint=f"{entity}_delete")
    def delete_record(record_id):
        with get_db() as conn:
            exists = conn.execute(f"SELECT 1 FROM {table} WHERE id=?", (record_id,)).fetchone()
        if not exists:
            return jsonify(error="Не найдено"), 404
        if before_delete and not before_delete(record_id):
            return jsonify(error=IN_USE_MSG), 409
        try:
            with get_db() as conn:
                conn.execute(f"DELETE FROM {table} WHERE id=?", (record_id,))
        except sqlite3.IntegrityError:
            return jsonify(error=IN_USE_MSG), 409
        return "", 204


def register_options(app, get_db, *, entity, sql):
    """/api/<entity>/options -> [{id, label}] для выпадающих списков."""
    @app.get(f"/api/{entity}/options", endpoint=f"{entity}_options")
    def options():
        with get_db() as conn:
            return jsonify([dict(r) for r in conn.execute(sql).fetchall()])
