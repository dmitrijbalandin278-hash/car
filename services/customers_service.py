"""Сервис «Клиенты». Порт 5002."""
import os

from flask import Flask, jsonify

from common import call, make_get_db, register_common, register_crud, register_options

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RENTALS_URL = os.environ.get("RENTALS_URL", "http://localhost:5003")

app = Flask(__name__)
app.config["DATABASE"] = os.environ.get("DATABASE", os.path.join(BASE_DIR, "..", "instance", "customers.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    driver_license TEXT NOT NULL
);
"""

get_db = make_get_db(app)
init_db = register_common(app, get_db, SCHEMA, "customers")


def customer_in_use(customer_id):
    status, data = call("GET", f"{RENTALS_URL}/internal/usage?customer_id={customer_id}")
    return status == 200 and data["count"] == 0


register_crud(
    app, get_db, entity="customers", table="customers",
    fields=["full_name", "phone", "email", "driver_license"],
    search=["full_name", "phone", "email", "driver_license"],
    list_sql="SELECT * FROM customers",
    before_delete=customer_in_use,
)

register_options(app, get_db, entity="customers",
                 sql="SELECT id, full_name AS label FROM customers ORDER BY full_name")


@app.get("/internal/customers/brief")
def customers_brief():
    with get_db() as conn:
        rows = conn.execute("SELECT id, full_name FROM customers").fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/api/customers/stats")
def customers_stats():
    with get_db() as conn:
        return jsonify(customers=conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5002)))
