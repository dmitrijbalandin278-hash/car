"""Сервис «Аренды». Порт 5003. Данные об автомобилях и клиентах берёт у соседних сервисов."""
import os

from flask import Flask, jsonify, request

from common import call, make_get_db, register_common, register_crud

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARS_URL = os.environ.get("CARS_URL", "http://localhost:5001")
CUSTOMERS_URL = os.environ.get("CUSTOMERS_URL", "http://localhost:5002")

app = Flask(__name__)
app.config["DATABASE"] = os.environ.get("DATABASE", os.path.join(BASE_DIR, "..", "instance", "rentals.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS rentals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Забронирована',
    total_price REAL NOT NULL CHECK(total_price >= 0),
    notes TEXT NOT NULL DEFAULT '',
    CHECK(end_date >= start_date)
);
"""

get_db = make_get_db(app)
init_db = register_common(app, get_db, SCHEMA, "rentals")


def check_refs(values):
    """Вместо FOREIGN KEY: проверяем, что автомобиль и клиент существуют в своих сервисах."""
    if "car_id" in values:
        status, _ = call("GET", f"{CARS_URL}/api/cars/{values['car_id']}")
        if status != 200:
            raise ValueError("Выбранная связанная запись не существует.")
    if "customer_id" in values:
        status, _ = call("GET", f"{CUSTOMERS_URL}/api/customers/{values['customer_id']}")
        if status != 200:
            raise ValueError("Выбранная связанная запись не существует.")


def enrich(rows):
    _, cars = call("GET", f"{CARS_URL}/internal/cars/brief")
    _, customers = call("GET", f"{CUSTOMERS_URL}/internal/customers/brief")
    car_map = {c["id"]: c for c in cars}
    cust_map = {c["id"]: c["full_name"] for c in customers}
    for r in rows:
        car = car_map.get(r["car_id"])
        r["car_name"] = f"{car['brand']} {car['model']} ({car['plate_number']})" if car else "—"
        r["customer_name"] = cust_map.get(r["customer_id"], "—")
    return rows


register_crud(
    app, get_db, entity="rentals", table="rentals",
    fields=["car_id", "customer_id", "start_date", "end_date", "status", "total_price", "notes"],
    search=["status", "start_date", "end_date"],
    list_sql="SELECT * FROM rentals",
    before_save=check_refs, enrich=enrich,
)


@app.get("/api/rentals/recent")
def recent():
    """Последние аренды для главной страницы."""
    limit = request.args.get("limit", 5, type=int)
    with get_db() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT id, car_id, customer_id, start_date, end_date, status "
            "FROM rentals ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
    _, cars = call("GET", f"{CARS_URL}/internal/cars/brief")
    _, customers = call("GET", f"{CUSTOMERS_URL}/internal/customers/brief")
    car_map = {c["id"]: f"{c['brand']} {c['model']}" for c in cars}
    cust_map = {c["id"]: c["full_name"] for c in customers}
    for r in rows:
        r["car_name"] = car_map.get(r["car_id"], "—")
        r["customer_name"] = cust_map.get(r["customer_id"], "—")
    return jsonify(rows)


@app.get("/api/rentals/stats")
def stats():
    with get_db() as conn:
        n = conn.execute("SELECT COUNT(*) FROM rentals WHERE status='Активна'").fetchone()[0]
    return jsonify(active_rentals=n)


@app.get("/internal/usage")
def usage():
    """Сколько аренд ссылается на автомобиль или клиента (для проверки перед удалением)."""
    with get_db() as conn:
        if request.args.get("car_id"):
            n = conn.execute("SELECT COUNT(*) FROM rentals WHERE car_id=?",
                             (request.args["car_id"],)).fetchone()[0]
        else:
            n = conn.execute("SELECT COUNT(*) FROM rentals WHERE customer_id=?",
                             (request.args.get("customer_id", 0),)).fetchone()[0]
    return jsonify(count=n)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5003)))
