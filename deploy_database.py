"""Apply schema.sql and load database/*.csv into the Railway Postgres instance."""

from __future__ import annotations

import csv
from pathlib import Path

import psycopg

from db import load_database_url

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schema.sql"
DATA_DIR = ROOT / "database"

TABLE_LOAD_ORDER = (
    ("tools", "tools.csv"),
    ("availability_slots", "availability_slots.csv"),
    ("students", "students.csv"),
    ("student_tools", "student_tools.csv"),
    ("student_availability", "student_availability.csv"),
)

DROP_TABLES_SQL = """
DROP TABLE IF EXISTS student_availability CASCADE;
DROP TABLE IF EXISTS student_tools CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS availability_slots CASCADE;
DROP TABLE IF EXISTS tools CASCADE;
"""


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SystemExit(f"{path.name} has no header row")
        columns = [name for name in reader.fieldnames if name]
        rows = [{column: (row.get(column) or "").strip() for column in columns} for row in reader]
    if not rows:
        raise SystemExit(f"{path.name} has no data rows")
    return columns, rows


def insert_rows(cursor: psycopg.Cursor, table: str, columns: list[str], rows: list[dict[str, str]]) -> int:
    placeholders = ", ".join(f"%({column})s" for column in columns)
    column_sql = ", ".join(columns)
    sql = (
        f"INSERT INTO {table} ({column_sql}) "
        f"OVERRIDING SYSTEM VALUE VALUES ({placeholders})"
    )
    cursor.executemany(sql, rows)
    return len(rows)


def reset_identity(cursor: psycopg.Cursor, table: str, column: str) -> None:
    cursor.execute(
        f"""
        SELECT setval(
            pg_get_serial_sequence(%s, %s),
            COALESCE((SELECT MAX({column}) FROM {table}), 1),
            true
        )
        """,
        (table, column),
    )


def main() -> None:
    database_url = load_database_url()
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(DROP_TABLES_SQL)
            cursor.execute(schema_sql)

            loaded: dict[str, int] = {}
            for table, filename in TABLE_LOAD_ORDER:
                columns, rows = read_csv_rows(DATA_DIR / filename)
                loaded[table] = insert_rows(cursor, table, columns, rows)

            reset_identity(cursor, "tools", "tool_id")
            reset_identity(cursor, "availability_slots", "availability_slot_id")
            reset_identity(cursor, "students", "student_id")

            cursor.execute("SELECT COUNT(*) FROM students")
            student_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM student_tools")
            tool_links = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM student_availability")
            availability_links = cursor.fetchone()[0]

        connection.commit()

    print("Deployed schema.sql and CSV seed data to Railway Postgres.")
    for table, count in loaded.items():
        print(f"  {table}: {count} rows")
    print(
        f"Verified counts: students={student_count}, "
        f"student_tools={tool_links}, student_availability={availability_links}"
    )


if __name__ == "__main__":
    main()
