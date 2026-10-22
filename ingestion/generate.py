"""Generate source files for one business date or a range.

    python -m ingestion.generate --date 2026-10-21          # one day
    python -m ingestion.generate --end 2026-10-21           # backfill from the opening export
    python -m ingestion.generate --start 2026-10-01 --end 2026-10-21
    python -m ingestion.generate --catch-up                 # every day not loaded yet, to yesterday

Files land in data/incoming/<YYYY-MM-DD>/. The output for a date never changes, so running
it twice is harmless.

--catch-up asks the database which business date was loaded last, so a daily job that missed
a few days fills the gap by itself. "Yesterday" is the Bali (WITA) calendar date.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ingestion.config import OPENING_DATE
from ingestion.simulator import build_world
from ingestion.sources import write_business_date

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "data" / "incoming"
LOCAL_TZ = ZoneInfo("Asia/Makassar")


def yesterday_local(now: datetime | None = None) -> date:
    """The last complete business day in Bali."""
    now = now or datetime.now(LOCAL_TZ)
    return now.astimezone(LOCAL_TZ).date() - timedelta(days=1)


def last_loaded_business_date() -> date | None:
    """Latest business date whose PMS reservation file loaded successfully."""
    from ingestion.db import connect  # only needed for --catch-up

    with connect() as conn:
        exists = conn.execute("select to_regclass('raw.load_log') is not null").fetchone()[0]
        if not exists:
            return None
        row = conn.execute(
            "select max(business_date) from raw.load_log"
            " where source = 'pms_reservations' and status = 'success'"
        ).fetchone()
    return row[0]


def catch_up_range(last_loaded: date | None, yesterday: date) -> tuple[date, date] | None:
    start = OPENING_DATE if last_loaded is None else last_loaded + timedelta(days=1)
    return None if start > yesterday else (start, yesterday)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--date", type=date.fromisoformat, help="single business date")
    ap.add_argument("--start", type=date.fromisoformat, default=OPENING_DATE)
    ap.add_argument("--end", type=date.fromisoformat, help="last business date (inclusive)")
    ap.add_argument("--catch-up", action="store_true", help="from last loaded date to yesterday")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    if args.catch_up:
        span = catch_up_range(last_loaded_business_date(), yesterday_local())
        if span is None:
            print("nothing to generate: data is already up to yesterday")
            return
        start, end = span
    elif args.date:
        start = end = args.date
    elif args.end:
        start, end = args.start, args.end
    else:
        ap.error("give --date, --end or --catch-up")

    world = build_world()
    d, total = start, 0
    while d <= end:
        written = write_business_date(world, d, args.out)
        total += sum(written.values())
        if start == end:
            for name, n in written.items():
                print(f"{d} {name}: {n} rows")
        d += timedelta(days=1)
    print(f"generated {start} .. {end}: {total} rows in {args.out}")


if __name__ == "__main__":
    main()
