"""Разовый перенос данных из старой общей БД instance/rental.db в базы микросервисов.
Запуск:  python migrate_data.py [путь/к/rental.db]
Сначала запустите сервисы хотя бы один раз (они создадут пустые таблицы)."""
import sqlite3
import sys
from pathlib import Path

old = Path(sys.argv[1] if len(sys.argv) > 1 else "instance/rental.db")
target_dir = Path("instance")
MAP = {
    "cars.db": ["categories", "cars"],
    "customers.db": ["customers"],
    "rentals.db": ["rentals"],
    "maintenance.db": ["maintenance"],
}
for db_name, tables in MAP.items():
    conn = sqlite3.connect(target_dir / db_name)
    conn.execute("ATTACH DATABASE ? AS old", (str(old),))
    for table in tables:
        conn.execute(f"DELETE FROM {table}")
        conn.execute(f"INSERT INTO {table} SELECT * FROM old.{table}")
        print(f"{db_name}: {table} перенесена")
    conn.commit()
    conn.close()
