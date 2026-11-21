"""Сервис «Обслуживание». Порт 5004."""
import os

from flask import Flask, jsonify, request

from common import call, make_get_db, register_common, register_crud

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARS_URL = os.environ.get("CARS_URL", "http://localhost:5001")

app = Flask(__name__)
app.config["DATABASE"] = os.environ.get("DATABASE", os.path.join(BASE_DIR, "..", "instance", "maintenance.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_id INTEGER NOT NULL,
    service_date TEXT NOT NULL,
    service_type TEXT NOT NULL,
    cost REAL NOT NULL CHECK(cost >= 0),
    notes TEXT NOT NULL DEFAULT ''
);
"""

get_db = make_get_db(app)
init_db = register_common(app, get_db, SCHEMA, "maintenance")


def check_refs(values):
    if "car_id" in values:
        status, _ = call("GET", f"{CARS_URL}/api/cars/{values['car_id']}")
        if status != 200:
            raise ValueError("Выбранная связанная запись не существует.")


def enrich(rows):
    _, cars = call("GET", f"{CARS_URL}/internal/cars/brief")
    car_map = {c["id"]: c for c in cars}
    for r in rows:
        car = car_map.get(r["car_id"])
        r["car_name"] = f"{car['brand']} {car['model']} ({car['plate_number']})" if car else "—"
    return rows


register_crud(
    app, get_db, entity="maintenance", table="maintenance",
    fields=["car_id", "service_date", "service_type", "cost", "notes"],
    search=["service_date", "service_type", "notes"],
    list_sql="SELECT * FROM maintenance",
    before_save=check_refs, enrich=enrich,
)


@app.get("/internal/usage")
def usage():
    with get_db() as conn:
        n = conn.execute("SELECT COUNT(*) FROM maintenance WHERE car_id=?",
                         (request.args.get("car_id", 0),)).fetchone()[0]
    return jsonify(count=n)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5004)))
