"""Apply every sql/*.sql file in name order. Each file must be safe to run more than once."""

from __future__ import annotations

from pathlib import Path

from ingestion.db import connect

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def main() -> None:
    files = sorted(SQL_DIR.glob("*.sql"))
    with connect() as conn:
        for path in files:
            conn.execute(path.read_text())
            print(f"applied {path.name}")


if __name__ == "__main__":
    main()
