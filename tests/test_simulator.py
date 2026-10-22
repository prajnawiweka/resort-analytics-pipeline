"""Business rules the simulated world must always respect."""

from collections import Counter

import pytest

from ingestion.config import PROPERTIES, REPORT_START
from ingestion.simulator import DAY, build_world, rng, room_type_capacity


@pytest.fixture(scope="module")
def world():
    return build_world()


def test_rng_depends_only_on_key():
    assert rng("stay", "2026-01-01", 1).random() == rng("stay", "2026-01-01", 1).random()
    assert rng("stay", "2026-01-01", 1).random() != rng("stay", "2026-01-02", 1).random()


def test_world_is_deterministic(world):
    build_world.cache_clear()
    again = build_world()
    assert [b.res_no for b in again.bookings] == [b.res_no for b in world.bookings]
    assert sum(b.total for b in again.bookings) == sum(b.total for b in world.bookings)


def test_reservation_numbers_are_unique(world):
    counts = Counter(b.res_no for b in world.bookings)
    assert counts.most_common(1)[0][1] == 1


def test_room_type_capacity_never_exceeded(world):
    nights = Counter()
    for b in world.bookings:
        if not b.is_cancelled:
            for k in range(b.nights):
                nights[b.room_type_id, b.check_in + k * DAY] += 1
    over = [(rt, d, n) for (rt, d), n in nights.items() if n > room_type_capacity(rt, d)]
    assert over == []


def test_booking_and_cancellation_order(world):
    for b in world.bookings:
        assert b.booked_at.date() <= b.check_in
        if b.cancelled_at:
            assert b.booked_at < b.cancelled_at
            assert b.cancelled_at.date() <= b.check_in


def test_night_audit_reconciles_with_reservations(world):
    revenue, sold = Counter(), Counter()
    for b in world.bookings:
        if not b.is_cancelled:
            for k in range(b.nights):
                key = (b.check_in + k * DAY, b.property_id)
                revenue[key] += b.rate
                sold[key] += 1
    for (d, pid), a in world.audit.items():
        assert a.room_revenue == revenue[d, pid]
        assert a.rooms_sold == sold[d, pid] <= a.rooms_available


def test_reviews_follow_completed_stays(world):
    by_res = {b.res_no: b for b in world.bookings}
    for rv in world.reviews:
        b = by_res[rv.res_no]
        assert not b.is_cancelled
        assert rv.submitted_at.date() >= b.check_out
        assert all(1 <= s <= 5 for s in rv.scores.values())


def test_targets_cover_every_property_month(world):
    for year in (2025, 2026, 2027):
        for p in PROPERTIES:
            for month in range(1, 13):
                revenue, occupancy = world.targets[year, month, p.id]
                assert revenue > 0 and 0 < occupancy < 1


def test_planted_patterns_are_visible(world):
    """The insights the dashboard is meant to surface really are in the data."""

    def share(year_month, pred):
        rows = [b for b in world.bookings if (b.check_in.year, b.check_in.month) == year_month]
        return sum(map(pred, rows)) / len(rows)

    direct = lambda b: b.channel_id in (1, 10)  # noqa: E731
    assert share((2026, 6), direct) > share((2025, 6), direct) + 0.03

    seminyak_clean = [
        rv.scores["cleanliness"]
        for rv in world.reviews
        if rv.property_id == 2 and rv.submitted_at.date() >= REPORT_START
    ]
    assert min(seminyak_clean) < 4
