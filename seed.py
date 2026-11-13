"""Заполнение базы тестовыми данными: python seed.py (пересоздаёт данные)."""
from datetime import date, timedelta
import random

from app import app, get_db, init_db

random.seed(7)

CATEGORIES = [
    ("Эконом", "Недорогие компактные автомобили для города"),
    ("Комфорт", "Седаны среднего класса"),
    ("Бизнес", "Представительские автомобили"),
    ("Внедорожник", "Кроссоверы и полноприводные авто"),
    ("Минивэн", "Вместительные авто для групп до 7 человек"),
    ("Электромобиль", "Автомобили с электрическим приводом"),
]

# марка, модель, класс(1-6), год, цена, КПП, топливо, пробег, состояние, доступен
CARS = [
    ("Lada", "Granta", 1, 2022, 1800, "Механика", "Бензин", 38000, "Хорошее", 1),
    ("Lada", "Vesta", 1, 2023, 2100, "Механика", "Бензин", 21000, "Отличное", 1),
    ("Hyundai", "Solaris", 1, 2021, 2200, "Автомат", "Бензин", 64000, "Хорошее", 1),
    ("Kia", "Rio", 1, 2022, 2300, "Автомат", "Бензин", 47000, "Хорошее", 0),
    ("Volkswagen", "Polo", 1, 2020, 2200, "Механика", "Бензин", 89000, "Удовлетворительное", 1),
    ("Toyota", "Camry", 2, 2022, 3800, "Автомат", "Бензин", 33000, "Отличное", 1),
    ("Kia", "K5", 2, 2023, 3900, "Автомат", "Бензин", 18000, "Отличное", 1),
    ("Skoda", "Octavia", 2, 2021, 3300, "Робот", "Бензин", 72000, "Хорошее", 1),
    ("Mazda", "6", 2, 2020, 3500, "Автомат", "Бензин", 95000, "Хорошее", 0),
    ("BMW", "530i", 3, 2022, 7500, "Автомат", "Бензин", 41000, "Отличное", 1),
    ("Mercedes-Benz", "E200", 3, 2021, 8200, "Автомат", "Бензин", 56000, "Хорошее", 1),
    ("Audi", "A6", 3, 2023, 8800, "Робот", "Дизель", 15000, "Отличное", 1),
    ("Toyota", "RAV4", 4, 2022, 4800, "Вариатор", "Бензин", 44000, "Хорошее", 1),
    ("Hyundai", "Tucson", 4, 2023, 5000, "Автомат", "Гибрид", 22000, "Отличное", 1),
    ("Toyota", "Land Cruiser Prado", 4, 2021, 9000, "Автомат", "Дизель", 78000, "Хорошее", 1),
    ("Mitsubishi", "Pajero Sport", 4, 2020, 6200, "Автомат", "Дизель", 102000, "Удовлетворительное", 0),
    ("Chevrolet", "Niva", 4, 2019, 2600, "Механика", "Бензин", 118000, "Удовлетворительное", 1),
    ("Volkswagen", "Caravelle", 5, 2021, 6800, "Робот", "Дизель", 83000, "Хорошее", 1),
    ("Tesla", "Model 3", 6, 2022, 6500, "Автомат", "Электро", 29000, "Отличное", 1),
    ("Hyundai", "Ioniq 5", 6, 2023, 7000, "Автомат", "Электро", 12000, "Отличное", 0),
]

CUSTOMERS = [
    ("Иванов Алексей Петрович", "+7 914 100-01-01", "ivanov.a@example.com"),
    ("Петрова Мария Сергеевна", "+7 914 100-02-02", "petrova.m@example.com"),
    ("Сидоров Дмитрий Андреевич", "+7 902 100-03-03", "sidorov.d@example.com"),
    ("Кузнецова Ольга Викторовна", "+7 908 100-04-04", "kuznetsova.o@example.com"),
    ("Смирнов Игорь Николаевич", "+7 950 100-05-05", "smirnov.i@example.com"),
    ("Попова Елена Александровна", "+7 924 100-06-06", "popova.e@example.com"),
    ("Васильев Сергей Олегович", "+7 914 100-07-07", "vasiliev.s@example.com"),
    ("Михайлова Анна Игоревна", "+7 902 100-08-08", "mikhailova.a@example.com"),
    ("Фёдоров Артём Денисович", "+7 908 100-09-09", "fedorov.a@example.com"),
    ("Морозова Татьяна Павловна", "+7 950 100-10-10", "morozova.t@example.com"),
    ("Волков Никита Евгеньевич", "+7 924 100-11-11", "volkov.n@example.com"),
    ("Алексеева Дарья Романовна", "+7 914 100-12-12", "alekseeva.d@example.com"),
    ("Лебедев Максим Владимирович", "+7 902 100-13-13", "lebedev.m@example.com"),
    ("Семёнова Ирина Борисовна", "+7 908 100-14-14", "semenova.i@example.com"),
    ("Егоров Павел Сергеевич", "+7 950 100-15-15", "egorov.p@example.com"),
    ("Козлова Юлия Андреевна", "+7 924 100-16-16", "kozlova.y@example.com"),
    ("Новиков Роман Алексеевич", "+7 914 100-17-17", "novikov.r@example.com"),
    ("Орлова Светлана Дмитриевна", "+7 902 100-18-18", "orlova.s@example.com"),
    ("Макаров Владислав Ильич", "+7 908 100-19-19", "makarov.v@example.com"),
    ("Захарова Полина Максимовна", "+7 950 100-20-20", "zakharova.p@example.com"),
]

SERVICES = [
    ("Замена масла и фильтров", 4500), ("Замена тормозных колодок", 6200),
    ("Шиномонтаж (сезонная замена)", 3200), ("Диагностика подвески", 2500),
    ("Замена ремня ГРМ", 14500), ("Мойка и химчистка салона", 3800),
    ("Замена аккумулятора", 9800), ("Плановое ТО", 7500),
    ("Ремонт кузова (локальная покраска)", 18000), ("Замена свечей зажигания", 3600),
]


def main():
    init_db()
    with get_db() as conn:
        for t in ("maintenance", "rentals", "customers", "cars", "categories"):
            conn.execute(f"DELETE FROM {t}")
        conn.execute("DELETE FROM sqlite_sequence")
        conn.executemany("INSERT INTO categories (name, description) VALUES (?,?)", CATEGORIES)
        for i, c in enumerate(CARS, 1):
            brand, model, cat, year, rate, kpp, fuel, km, cond, avail = c
            plate = f"{random.choice('ABEKMHOPCTYX')}{random.randint(100, 999)}{random.choice('ABEKMHOPCTYX')}{random.choice('ABEKMHOPCTYX')}38"
            vin = f"XW{i:02d}{random.randint(10**10, 10**11 - 1)}{year % 100:02d}"
            conn.execute(
                "INSERT INTO cars (brand, model, plate_number, vin, year, category_id, daily_rate, transmission, fuel, mileage, condition, available, description) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (brand, model, plate, vin, year, cat, rate, kpp, fuel, km, cond, avail, f"{brand} {model}, {year} г., {kpp.lower()}, {fuel.lower()}."))
        for i, (name, phone, email) in enumerate(CUSTOMERS, 1):
            conn.execute("INSERT INTO customers (full_name, phone, email, driver_license) VALUES (?,?,?,?)",
                         (name, phone, email, f"38 {random.randint(10, 25)} {random.randint(100000, 999999)}"))
        today = date(2026, 11, 13)
        for i in range(20):
            car_id = i + 1
            rate = CARS[i][4]
            days = random.randint(1, 10)
            offset = random.randint(-40, 25)
            start = today + timedelta(days=offset)
            end = start + timedelta(days=days)
            if end < today:
                status = "Отменена" if i % 7 == 0 else "Завершена"
            elif start > today:
                status = "Забронирована"
            else:
                status = "Активна"
            conn.execute(
                "INSERT INTO rentals (car_id, customer_id, start_date, end_date, status, total_price, notes) VALUES (?,?,?,?,?,?,?)",
                (car_id, random.randint(1, 20), start.isoformat(), end.isoformat(), status, rate * max(days, 1),
                 random.choice(["", "", "Детское кресло", "Выдача в аэропорту", "Второй водитель", "Полная страховка"])))
        for i in range(20):
            svc, cost = SERVICES[i % len(SERVICES)]
            conn.execute("INSERT INTO maintenance (car_id, service_date, service_type, cost, notes) VALUES (?,?,?,?,?)",
                         (random.randint(1, 20), (today - timedelta(days=random.randint(3, 200))).isoformat(), svc, cost,
                          random.choice(["", "Плановое обслуживание", "По пробегу", "Выполнено в срок"])))
    print("Готово: 6 классов, 20 автомобилей, 20 клиентов, 20 аренд, 20 записей обслуживания.")


if __name__ == "__main__":
    main()
