import pytest
from app import app as flask_app, init_db


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.sqlite"
    flask_app.config.update(TESTING=True, DATABASE=str(db_path), SECRET_KEY="test-secret")
    init_db()
    with flask_app.test_client() as client:
        yield client


def seed_category(client):
    return client.post("/categories/new", data={"name": "Седан", "description": "Комфортные городские автомобили"}, follow_redirects=True)


def car_data(**overrides):
    data = {
        "brand": "Toyota", "model": "Camry", "plate_number": "A123BC38", "vin": "JTNB11HK000000001",
        "year": "2022", "category_id": "1", "daily_rate": "3500", "transmission": "Автомат",
        "fuel": "Бензин", "mileage": "25000", "condition": "Хорошее", "available": "on",
        "description": "Тестовый автомобиль",
    }
    data.update(overrides)
    return data


def seed_car(client):
    seed_category(client)
    return client.post("/cars/new", data=car_data(), follow_redirects=True)


def seed_customer(client):
    return client.post("/customers/new", data={
        "full_name": "Иван Иванов", "phone": "+7 900 000-00-00",
        "email": "ivan@example.com", "driver_license": "38 00 000001"
    }, follow_redirects=True)


def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Система проката автомобилей".encode() in response.data


def test_category_create_read_update_delete(client):
    response = seed_category(client)
    assert response.status_code == 200
    assert "Седан".encode() in response.data
    response = client.post("/categories/1/edit", data={"name": "Внедорожник", "description": "Обновлено"}, follow_redirects=True)
    assert "Внедорожник".encode() in response.data
    response = client.post("/categories/1/delete", follow_redirects=True)
    assert "Записи не найдены".encode() in response.data


def test_car_create_read_update_delete(client):
    seed_car(client)
    response = client.get("/cars")
    assert "Camry".encode() in response.data
    assert "A123BC38".encode() in response.data
    response = client.post("/cars/1/edit", data=car_data(model="Camry Hybrid", daily_rate="4200", fuel="Гибрид"), follow_redirects=True)
    assert "Camry Hybrid".encode() in response.data
    response = client.post("/cars/1/delete", follow_redirects=True)
    assert "Записи не найдены".encode() in response.data


def test_car_search_by_plate(client):
    seed_car(client)
    assert "Camry".encode() in client.get("/cars?q=A123").data
    assert "Записи не найдены".encode() in client.get("/cars?q=ZZZ").data


def test_customer_create_read_update_delete(client):
    seed_customer(client)
    assert "Иван Иванов".encode() in client.get("/customers").data
    response = client.post("/customers/1/edit", data={
        "full_name": "Пётр Петров", "phone": "+7 911 111-11-11",
        "email": "petr@example.com", "driver_license": "38 00 000002"
    }, follow_redirects=True)
    assert "Пётр Петров".encode() in response.data
    response = client.post("/customers/1/delete", follow_redirects=True)
    assert "Записи не найдены".encode() in response.data


def test_rental_create_read_update_delete(client):
    seed_car(client)
    seed_customer(client)
    data = {"car_id": "1", "customer_id": "1", "start_date": "2026-10-10",
            "end_date": "2026-10-12", "status": "Забронирована", "total_price": "7000", "notes": ""}
    client.post("/rentals/new", data=data, follow_redirects=True)
    assert "Camry".encode() in client.get("/rentals").data
    data["status"] = "Активна"
    response = client.post("/rentals/1/edit", data=data, follow_redirects=True)
    assert "Активна".encode() in response.data
    response = client.post("/rentals/1/delete", follow_redirects=True)
    assert "Записи не найдены".encode() in response.data


def test_maintenance_create_read_update_delete(client):
    seed_car(client)
    data = {"car_id": "1", "service_date": "2026-10-01", "service_type": "Замена масла",
            "cost": "5500", "notes": "Плановое ТО"}
    client.post("/maintenance/new", data=data, follow_redirects=True)
    assert "Замена масла".encode() in client.get("/maintenance").data
    data["service_type"] = "Замена колодок"
    response = client.post("/maintenance/1/edit", data=data, follow_redirects=True)
    assert "Замена колодок".encode() in response.data
    response = client.post("/maintenance/1/delete", follow_redirects=True)
    assert "Записи не найдены".encode() in response.data


def test_invalid_rental_dates_are_rejected(client):
    seed_car(client)
    seed_customer(client)
    response = client.post("/rentals/new", data={
        "car_id": "1", "customer_id": "1", "start_date": "2026-10-15",
        "end_date": "2026-10-10", "status": "Забронирована", "total_price": "100"
    }, follow_redirects=True)
    assert "Дата окончания не может быть раньше даты начала".encode() in response.data


def test_negative_price_is_rejected(client):
    seed_category(client)
    response = client.post("/cars/new", data=car_data(daily_rate="-5"), follow_redirects=True)
    assert "не может быть отрицательным".encode() in response.data


def test_duplicate_plate_is_rejected(client):
    seed_car(client)
    response = client.post("/cars/new", data=car_data(), follow_redirects=True)
    assert "уникальным значением".encode() in response.data


def test_invalid_year_is_rejected(client):
    seed_category(client)
    response = client.post("/cars/new", data=car_data(year="1800"), follow_redirects=True)
    assert "Проверьте корректность".encode() in response.data
    response = client.post("/cars/new", data=car_data(year="20.5"), follow_redirects=True)
    assert "целым числом".encode() in response.data
