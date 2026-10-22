"""Fail when the marts are not up to date.

    python -m ingestion.check_freshness              # data must reach yesterday (WITA)
    python -m ingestion.check_freshness --max-lag 2  # allow two days of delay

Run after `dbt build` in the daily job: a green run must mean the dashboard shows yesterday.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from ingestion.db import connect
from ingestion.generate import yesterday_local


def lag_days(data_as_of: date | None, yesterday: date) -> int | None:
    return None if data_as_of is None else (yesterday - data_as_of).days


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--max-lag", type=int, default=0, help="days behind yesterday allowed")
    args = ap.parse_args(argv)

    with connect() as conn:
        data_as_of = conn.execute("select data_as_of from marts.data_freshness").fetchone()[0]
    yesterday = yesterday_local()
    lag = lag_days(data_as_of, yesterday)
    if lag is None:
        print("FAIL: marts.data_freshness is empty", file=sys.stderr)
        return 1
    if lag > args.max_lag:
        print(f"FAIL: data as of {data_as_of}, expected {yesterday} ({lag} days late)",
              file=sys.stderr)  # fmt: skip
        return 1
    print(f"OK: data as of {data_as_of} (yesterday in Bali: {yesterday})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
