"""Generate source files for one business date or a range.

    python -m ingestion.generate --date 2026-10-21          # one day
    python -m ingestion.generate --end 2026-10-21           # backfill from the opening export
    python -m ingestion.generate --start 2026-10-01 --end 2026-10-21

Files land in data/incoming/<YYYY-MM-DD>/. The output for a date never changes, so running
it twice is harmless.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

from ingestion.config import OPENING_DATE
from ingestion.simulator import build_world
from ingestion.sources import write_business_date

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "data" / "incoming"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--date", type=date.fromisoformat, help="single business date")
    ap.add_argument("--start", type=date.fromisoformat, default=OPENING_DATE)
    ap.add_argument("--end", type=date.fromisoformat, help="last business date (inclusive)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    if args.date:
        start = end = args.date
    elif args.end:
        start, end = args.start, args.end
    else:
        ap.error("give --date or --end")

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
