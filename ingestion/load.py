"""Load source files from data/incoming/ into the raw schema.

    python -m ingestion.load                 # every file not loaded yet
    python -m ingestion.load --date 2026-10-21
    python -m ingestion.load --force         # reload even unchanged files

Rules
* Each file loads in one transaction: its previous rows are deleted, then all rows are inserted.
  A failed file leaves the database exactly as it was.
* A file whose content (sha256) already loaded successfully is skipped, so reruns are safe.
* Every attempt, successful or not, is written to raw.load_log.
* An unexpected CSV header stops the load: a changed source format must be noticed, not guessed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import psycopg
from openpyxl import load_workbook

from ingestion.db import connect
from ingestion.sources import PMS_AUDIT_COLUMNS, PMS_RESERVATION_COLUMNS

DEFAULT_IN = Path(__file__).resolve().parent.parent / "data" / "incoming"
META = ["_load_id", "_source_file", "_row_number"]


class SourceFormatError(Exception):
    """The file does not look like what this source is supposed to send."""


@dataclass(frozen=True)
class Feed:
    source: str
    table: str
    pattern: re.Pattern


FEEDS = [
    Feed("pms_reservations", "raw.pms_reservations", re.compile(r"pms_reservations\.csv")),
    Feed("pms_night_audit", "raw.pms_night_audit", re.compile(r"pms_night_audit\.csv")),
    Feed("ota_bookings", "raw.ota_bookings", re.compile(r"ota_bookings\.json")),
    Feed("reviews", "raw.reviews", re.compile(r"reviews\.json")),
    Feed("finance_targets", "raw.finance_targets", re.compile(r"finance_targets_\d{4}\.xlsx")),
]


# ----------------------------------------------------------------------------- readers
def read_csv(path: Path, expected: list[str]) -> tuple[list[str], Iterator[list]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != expected:
            raise SourceFormatError(f"{path.name}: header {header} does not match {expected}")
        rows = [row for row in reader]
    columns = [c.lower() for c in expected]
    return columns, ([*row, i] for i, row in enumerate(rows, start=1))


def read_json_items(path: Path, envelope_key: str | None) -> Iterator[list]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload[envelope_key] if envelope_key else payload
    if not isinstance(items, list):
        raise SourceFormatError(f"{path.name}: expected a list of records")
    for i, item in enumerate(items, start=1):
        yield [json.dumps(item, ensure_ascii=False), i]


def read_finance_workbook(path: Path) -> Iterator[list]:
    wb = load_workbook(path, read_only=True)
    for ws in wb.worksheets:
        header: list[str] | None = None
        for excel_row, values in enumerate(ws.iter_rows(values_only=True), start=1):
            if header is None:
                if values and values[0] == "Property":
                    header = [str(v) for v in values]
                continue
            if all(v is None for v in values):
                continue
            record = {h: v for h, v in zip(header, values, strict=False)}
            yield [ws.title, json.dumps(record, default=str), excel_row]
        if header is None:
            raise SourceFormatError(f"{path.name}: sheet {ws.title!r} has no 'Property' header")


def rows_for(feed: Feed, path: Path) -> tuple[list[str], Iterator[list]]:
    if feed.source == "pms_reservations":
        return read_csv(path, PMS_RESERVATION_COLUMNS)
    if feed.source == "pms_night_audit":
        return read_csv(path, PMS_AUDIT_COLUMNS)
    if feed.source == "ota_bookings":
        return ["record"], read_json_items(path, "bookings")
    if feed.source == "reviews":
        return ["record"], read_json_items(path, None)
    return ["sheet_name", "record"], read_finance_workbook(path)


# ----------------------------------------------------------------------------- loading
@dataclass
class Result:
    file: str
    status: str  # loaded | skipped | failed
    rows: int = 0
    error: str = ""


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def already_loaded(conn: psycopg.Connection, source_file: str, digest: str) -> bool:
    row = conn.execute(
        "select 1 from raw.load_log where source_file = %s and file_sha256 = %s"
        " and status = 'success' limit 1",
        (source_file, digest),
    ).fetchone()
    return row is not None


def load_file(
    conn: psycopg.Connection, feed: Feed, path: Path, business_date: date, force: bool = False
) -> Result:
    source_file = f"{business_date.isoformat()}/{path.name}"
    digest = sha256_of(path)
    if not force and already_loaded(conn, source_file, digest):
        return Result(source_file, "skipped")

    started = datetime.now(timezone.utc)
    try:
        with conn.transaction():
            load_id = conn.execute(
                "insert into raw.load_log (business_date, source, source_file, file_sha256,"
                " status, started_at) values (%s, %s, %s, %s, 'success', %s) returning load_id",
                (business_date, feed.source, source_file, digest, started),
            ).fetchone()[0]
            conn.execute(f"delete from {feed.table} where _source_file = %s", (source_file,))
            columns, rows = rows_for(feed, path)
            n = 0
            cols = ", ".join([*columns, *META])
            with conn.cursor().copy(f"copy {feed.table} ({cols}) from stdin") as copy:
                for row in rows:
                    *values, row_number = row
                    copy.write_row([*values, load_id, source_file, row_number])
                    n += 1
            conn.execute(
                "update raw.load_log set rows_loaded = %s, finished_at = now() where load_id = %s",
                (n, load_id),
            )
        return Result(source_file, "loaded", n)
    except (SourceFormatError, psycopg.Error, ValueError, KeyError) as exc:
        with conn.transaction():
            conn.execute(
                "insert into raw.load_log (business_date, source, source_file, file_sha256,"
                " status, error, started_at) values (%s, %s, %s, %s, 'failed', %s, %s)",
                (business_date, feed.source, source_file, digest, str(exc)[:2000], started),
            )
        return Result(source_file, "failed", error=str(exc))


def discover(incoming: Path, only: date | None = None) -> Iterator[tuple[date, Feed, Path]]:
    for folder in sorted(p for p in incoming.iterdir() if p.is_dir()):
        try:
            business_date = date.fromisoformat(folder.name)
        except ValueError:
            continue
        if only and business_date != only:
            continue
        for path in sorted(folder.iterdir()):
            feed = next((f for f in FEEDS if f.pattern.fullmatch(path.name)), None)
            if feed:
                yield business_date, feed, path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--date", type=date.fromisoformat, help="load only this business date")
    ap.add_argument("--incoming", type=Path, default=DEFAULT_IN)
    ap.add_argument("--force", action="store_true", help="reload files even if unchanged")
    args = ap.parse_args(argv)

    counts = {"loaded": 0, "skipped": 0, "failed": 0}
    rows = 0
    with connect() as conn:
        conn.autocommit = True  # each file manages its own transaction
        for business_date, feed, path in discover(args.incoming, args.date):
            res = load_file(conn, feed, path, business_date, args.force)
            counts[res.status] += 1
            rows += res.rows
            if res.status == "failed":
                print(f"FAILED {res.file}: {res.error}", file=sys.stderr)
    print(f"loaded {counts['loaded']} files ({rows} rows), skipped {counts['skipped']}, "
          f"failed {counts['failed']}")  # fmt: skip
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
