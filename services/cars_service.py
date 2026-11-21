"""Сервис «Автомобили» (+ классы автомобилей). Порт 5001."""
import os

from flask import Flask, jsonify

from common import (call, make_get_db, register_common, register_crud, register_options)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RENTALS_URL = os.environ.get("RENTALS_URL", "http://localhost:5003")
MAINTENANCE_URL = os.environ.get("MAINTENANCE_URL", "http://localhost:5004")

app = Flask(__name__)
app.config["DATABASE"] = os.environ.get("DATABASE", os.path.join(BASE_DIR, "..", "instance", "cars.db"))

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    plate_number TEXT NOT NULL UNIQUE,
    vin TEXT NOT NULL DEFAULT '',
    year INTEGER NOT NULL CHECK(year BETWEEN 1950 AND 2100),
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    daily_rate REAL NOT NULL CHECK(daily_rate >= 0),
    transmission TEXT NOT NULL DEFAULT 'Автомат',
    fuel TEXT NOT NULL DEFAULT 'Бензин',
    mileage INTEGER NOT NULL DEFAULT 0 CHECK(mileage >= 0),
    condition TEXT NOT NULL DEFAULT 'Хорошее',
    available INTEGER NOT NULL DEFAULT 1,
    description TEXT NOT NULL DEFAULT ''
);
"""

get_db = make_get_db(app)
init_db = register_common(app, get_db, SCHEMA, "cars")


def car_in_use(car_id):
    """Автомобиль нельзя удалить, если есть аренды или обслуживание (раньше это делал FOREIGN KEY)."""
    for base in (RENTALS_URL, MAINTENANCE_URL):
        status, data = call("GET", f"{base}/internal/usage?car_id={car_id}")
        if status != 200 or data["count"] > 0:
            return False
    return True


register_crud(
    app, get_db, entity="categories", table="categories",
    fields=["name", "description"], search=["name", "description"],
    list_sql="SELECT * FROM categories",
)

register_crud(
    app, get_db, entity="cars", table="cars",
    fields=["brand", "model", "plate_number", "vin", "year", "category_id", "daily_rate",
            "transmission", "fuel", "mileage", "condition", "available", "description"],
    search=["brand", "model", "plate_number", "vin"],
    list_sql="""SELECT t.*, c.name AS category_name,
                CASE WHEN t.available=1 THEN 'Доступен' ELSE 'Недоступен' END AS available_label
                FROM cars t JOIN categories c ON c.id=t.category_id""",
    before_delete=car_in_use,
)

register_options(app, get_db, entity="categories",
                 sql="SELECT id, name AS label FROM categories ORDER BY name")
register_options(app, get_db, entity="cars",
                 sql="SELECT id, brand || ' ' || model || ' (' || plate_number || ')' AS label "
                     "FROM cars ORDER BY brand, model")


@app.get("/internal/cars/brief")
def cars_brief():
    with get_db() as conn:
        rows = conn.execute("SELECT id, brand, model, plate_number FROM cars").fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/api/cars/stats")
def cars_stats():
    with get_db() as conn:
        return jsonify(
            cars=conn.execute("SELECT COUNT(*) FROM cars").fetchone()[0],
            available=conn.execute("SELECT COUNT(*) FROM cars WHERE available=1").fetchone()[0],
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
