"""Date logic used by the daily job."""

from datetime import UTC, date, datetime

from ingestion.check_freshness import lag_days
from ingestion.config import OPENING_DATE
from ingestion.generate import catch_up_range, yesterday_local


def test_yesterday_follows_bali_calendar():
    # 22:17 UTC on 21 Oct is 06:17 WITA on 22 Oct, so yesterday in Bali is 21 Oct
    assert yesterday_local(datetime(2026, 10, 21, 22, 17, tzinfo=UTC)) == date(2026, 10, 21)
    # 15:00 UTC on 21 Oct is 23:00 WITA on 21 Oct, so yesterday is still 20 Oct
    assert yesterday_local(datetime(2026, 10, 21, 15, 0, tzinfo=UTC)) == date(2026, 10, 20)


def test_catch_up_starts_after_last_load():
    assert catch_up_range(date(2026, 10, 18), date(2026, 10, 21)) == (
        date(2026, 10, 19),
        date(2026, 10, 21),
    )


def test_catch_up_on_empty_database_backfills_everything():
    assert catch_up_range(None, date(2026, 10, 21)) == (OPENING_DATE, date(2026, 10, 21))


def test_catch_up_when_already_current():
    assert catch_up_range(date(2026, 10, 21), date(2026, 10, 21)) is None


def test_freshness_lag():
    assert lag_days(date(2026, 10, 21), date(2026, 10, 21)) == 0
    assert lag_days(date(2026, 10, 19), date(2026, 10, 21)) == 2
    assert lag_days(None, date(2026, 10, 21)) is None
