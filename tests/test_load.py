"""Loader guarantees: reruns are safe, failures leave no partial data, every attempt is logged.

Uses business date 1999-01-01, which no real file has, and removes its rows afterwards.
"""

import shutil
from datetime import date

import pytest

from ingestion.db import connect
from ingestion.load import FEEDS, load_file
from ingestion.simulator import build_world
from ingestion.sources import write_business_date

TEST_DATE = date(1999, 1, 1)
RESERVATIONS = next(f for f in FEEDS if f.source == "pms_reservations")


@pytest.fixture
def conn():
    with connect() as c:
        c.autocommit = True
        yield c
        c.execute("delete from raw.pms_reservations where _source_file like '1999-01-01/%'")
        c.execute("delete from raw.load_log where business_date = %s", (TEST_DATE,))


@pytest.fixture
def csv_file(tmp_path):
    write_business_date(build_world(), date(2026, 3, 10), tmp_path)
    path = tmp_path / TEST_DATE.isoformat() / "pms_reservations.csv"
    path.parent.mkdir()
    shutil.copy(tmp_path / "2026-03-10" / "pms_reservations.csv", path)
    return path


def raw_rows(conn):
    return conn.execute(
        "select count(*) from raw.pms_reservations where _source_file like '1999-01-01/%'"
    ).fetchone()[0]


def test_rerun_skips_unchanged_file(conn, csv_file):
    first = load_file(conn, RESERVATIONS, csv_file, TEST_DATE)
    second = load_file(conn, RESERVATIONS, csv_file, TEST_DATE)
    assert first.status == "loaded" and first.rows > 0
    assert second.status == "skipped"
    assert raw_rows(conn) == first.rows


def test_force_and_changed_file_replace_rows(conn, csv_file):
    first = load_file(conn, RESERVATIONS, csv_file, TEST_DATE)
    forced = load_file(conn, RESERVATIONS, csv_file, TEST_DATE, force=True)
    assert forced.status == "loaded" and raw_rows(conn) == first.rows

    lines = csv_file.read_text().splitlines(keepends=True)
    csv_file.write_text("".join(lines[:-1]))  # source resends the file with one row fewer
    changed = load_file(conn, RESERVATIONS, csv_file, TEST_DATE)
    assert changed.status == "loaded" and raw_rows(conn) == first.rows - 1


def test_bad_header_fails_cleanly(conn, csv_file):
    load_file(conn, RESERVATIONS, csv_file, TEST_DATE)
    before = raw_rows(conn)
    text = csv_file.read_text().replace("GUEST_EMAIL", "EMAIL", 1)
    csv_file.write_text(text)

    result = load_file(conn, RESERVATIONS, csv_file, TEST_DATE)

    assert result.status == "failed" and "header" in result.error
    assert raw_rows(conn) == before  # previous good load untouched
    status = conn.execute(
        "select status from raw.load_log where business_date = %s order by load_id desc limit 1",
        (TEST_DATE,),
    ).fetchone()[0]
    assert status == "failed"
