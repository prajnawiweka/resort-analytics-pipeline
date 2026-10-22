"""Simulates the "real world" of the resort group: every reservation, stay, review and target
from SIM_START to HORIZON.

The world is simulated once and is fully deterministic. Each daily source extract is a view of
that world as of one business date (see sources.py), so running the generator for a later date
never changes what earlier dates contained.

Randomness is drawn from small generators keyed by what they describe (a stay date and room
type, a booking, an audit date), not from one global stream. Extending the horizon therefore
leaves earlier results untouched.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import lru_cache

from ingestion.config import (
    BASE_MIX,
    CH,
    CHANNELS,
    DIRECT_CAMPAIGN_START,
    FIRST_NAMES,
    HORIZON,
    LAST_NAMES,
    MIX_TILT,
    PROP,
    PROPERTIES,
    REPORT_START,
    REVIEW_TEXTS,
    ROOM_TYPES,
    RT,
    SEED,
    SEMINYAK_CLEANLINESS_DIP,
    SEMINYAK_RENOVATION,
    SIM_START,
    SPEND_FACTOR,
    UBUD_ROOFTOP_OPENING,
    WESTERN_FIRST,
    WESTERN_LAST,
)

DAY = timedelta(days=1)


# ----------------------------------------------------------------------------- randomness
def _digest(*key: object) -> bytes:
    return hashlib.sha256("|".join(map(str, (SEED, *key))).encode()).digest()


def rng(*key: object) -> random.Random:
    """A random generator whose sequence depends only on `key`."""
    return random.Random(int.from_bytes(_digest(*key)[:8], "big"))


def stable_int(*key: object, digits: int = 9) -> int:
    return int.from_bytes(_digest(*key)[:8], "big") % 10**digits


def pick_weighted(r: random.Random, weights: dict) -> object:
    keys = list(weights)
    return r.choices(keys, weights=[weights[k] for k in keys])[0]


# ----------------------------------------------------------------------------- data classes
@dataclass
class Guest:
    id: int
    first_name: str
    last_name: str
    email: str
    country: str  # ISO alpha-2
    created_at: datetime


@dataclass
class Booking:
    res_no: str
    property_id: int
    room_type_id: int
    channel_id: int
    guest_id: int
    check_in: date
    nights: int
    adults: int
    children: int
    rate: int  # USD per night
    booked_at: datetime  # local time (WITA)
    cancelled_at: datetime | None
    ota_ref: str | None = None
    ota_link_missing: bool = False  # channel manager forgot the PMS reservation number

    @property
    def check_out(self) -> date:
        return self.check_in + self.nights * DAY

    @property
    def total(self) -> int:
        return self.rate * self.nights

    @property
    def is_cancelled(self) -> bool:
        return self.cancelled_at is not None


@dataclass
class Review:
    review_id: str
    platform: str
    property_id: int
    res_no: str
    submitted_at: datetime  # local time (WITA)
    scores: dict[str, float]  # 1-5 scale; platforms may publish another scale
    text: str
    reviewer_country: str  # ISO alpha-2


@dataclass
class AuditDay:
    audit_date: date
    property_id: int
    rooms_available: int
    rooms_sold: int
    room_revenue: int
    fnb_revenue: int
    spa_revenue: int
    other_revenue: int


@dataclass
class World:
    guests: list[Guest]
    bookings: list[Booking]
    reviews: list[Review]
    audit: dict[tuple[date, int], AuditDay]
    targets: dict[tuple[int, int, int], tuple[int, float]]  # (year, month, pid) -> (rev, occ)
    _by_booked_date: dict[date, list[Booking]] = field(default_factory=dict)
    _by_cancel_date: dict[date, list[Booking]] = field(default_factory=dict)
    _reviews_by_date: dict[date, list[Review]] = field(default_factory=dict)


# ----------------------------------------------------------------------------- demand model
def season(d: date, pid: int) -> float:
    m = d.month
    s = {1: .95, 2: .78, 3: .84, 4: .92, 5: .96, 6: 1.06, 7: 1.20, 8: 1.22, 9: 1.04, 10: .97,
         11: .83, 12: 1.08}[m]  # fmt: skip
    if (m == 12 and d.day >= 20) or (m == 1 and d.day <= 5):
        s *= 1.12
    if pid == 4 and m in (6, 7, 12):
        s *= 1.07
    if pid == 3 and m in (5, 6, 7, 8, 9):
        s *= 1.05
    if d.weekday() in (4, 5):
        s *= 1.04
    if d.year >= 2026:
        s *= {3: 1.12, 5: 1.08, 2: 1.00}.get(pid, 1.05)
    if d.year >= 2027:
        s *= 1.03
    return s


def rate_multiplier(d: date) -> float:
    m = d.month
    r = {1: 1.02, 2: .88, 3: .92, 4: .97, 5: .99, 6: 1.08, 7: 1.22, 8: 1.25, 9: 1.06, 10: 1,
         11: .90, 12: 1.15}[m]  # fmt: skip
    if (m == 12 and d.day >= 20) or (m == 1 and d.day <= 5):
        r *= 1.15
    if d.year >= 2026:
        r *= 1.06
    if d.year >= 2027:
        r *= 1.04
    return r


def channel_weights(d: date) -> dict[int, float]:
    k = max(0.0, min(1.0, (d - DIRECT_CAMPAIGN_START).days / 120))
    return {1: .12 + .07 * k, 2: .26 - .04 * k, 3: .13 - .02 * k, 4: .14 - .02 * k,
            5: .06 + .01 * k, 6: .05 + .02 * k, 7: .08, 8: .07 - .01 * k, 9: .04 - .01 * k,
            10: .05}  # fmt: skip


def renovating(d: date) -> bool:
    return SEMINYAK_RENOVATION[0] <= d <= SEMINYAK_RENOVATION[1]


def rooms_available(pid: int, d: date) -> int:
    return PROP[pid].rooms - (10 if pid == 2 and renovating(d) else 0)


def room_type_capacity(rid: int, d: date) -> int:
    return RT[rid].count - (10 if rid == 5 and renovating(d) else 0)


COUNTRY_MIX = {pid: {c: w * MIX_TILT[pid].get(c, 1) for c, w in BASE_MIX.items()} for pid in PROP}
LOS_MEAN = {1: 3.6, 2: 3.2, 3: 4.4, 4: 4.0, 5: 3.4}


def length_of_stay(r: random.Random, pid: int) -> int:
    gamma = LOS_MEAN[pid] / 3 * sum(r.expovariate(1) for _ in range(3))
    return max(1, min(14, round(gamma)))


# ----------------------------------------------------------------------------- simulation
def _simulate_bookings() -> tuple[list[Guest], list[Booking]]:
    guests: list[Guest] = []
    by_country: dict[str, list[int]] = defaultdict(list)

    def get_guest(r: random.Random, country: str, when: datetime) -> int:
        pool = by_country[country]
        if pool and r.random() < 0.18:
            return r.choice(pool)
        gid = len(guests) + 1
        first = r.choice(FIRST_NAMES.get(country, WESTERN_FIRST))
        last = r.choice(LAST_NAMES.get(country, WESTERN_LAST))
        email = f"{first}.{last}".lower().replace(" ", "") + f"{gid}@example.com"
        guests.append(Guest(gid, first, last, email, country, when))
        pool.append(gid)
        return gid

    n_days = (HORIZON - SIM_START).days + 1
    occupied = {rt.id: [0] * (n_days + 20) for rt in ROOM_TYPES}
    bookings: list[Booking] = []

    for di in range(n_days):
        t = SIM_START + di * DAY
        for p in PROPERTIES:
            target = min(0.97, p.base_occ * season(t, p.id))
            rts = [rt for rt in ROOM_TYPES if rt.property_id == p.id]
            min_rate = min(rt.base_rate for rt in rts)
            seq = 0
            for rt in rts:
                r = rng("stay", t, rt.id)
                premium = 1 - 0.05 * (rt.base_rate - min_rate) / 200
                lam = target * premium * room_type_capacity(rt.id, t) / 3.6 * 1.25
                trials = int(lam * 2 + 3)
                arrivals = sum(r.random() < lam / trials for _ in range(trials))
                for _ in range(arrivals):
                    nights = length_of_stay(r, p.id)
                    ch = CH[pick_weighted(r, channel_weights(t))]
                    lead = int(r.expovariate(1 / ch.lead_mean))
                    booked_day = t - lead * DAY
                    cancelled = r.random() < ch.cancel_prob * (1.15 if lead > 60 else 1)
                    if not cancelled:
                        nights_idx = range(di, di + nights)
                        if any(
                            occupied[rt.id][k] >= room_type_capacity(rt.id, t + (k - di) * DAY)
                            for k in nights_idx
                        ):
                            continue  # sold out: the guest books elsewhere
                        for k in nights_idx:
                            occupied[rt.id][k] += 1
                    booked_at = datetime.combine(booked_day, datetime.min.time()) + timedelta(
                        minutes=r.randint(0, 1439)
                    )
                    country = pick_weighted(r, COUNTRY_MIX[p.id])
                    gid = get_guest(r, country, booked_at)
                    if rt.max_occupancy > 2:
                        adults = min(rt.max_occupancy, r.choice([1, 2, 2, 2, 2, 3, 4]))
                    else:
                        adults = min(rt.max_occupancy, r.choice([1, 2, 2, 2]))
                    children = 0
                    if rt.max_occupancy > adults:
                        kids = r.choice([0, 0, 1, 2]) if p.id == 4 else r.choice([0, 0, 0, 1])
                        children = min(kids, rt.max_occupancy - adults)
                    spend = SPEND_FACTOR.get(country, 1) ** 0.3
                    rate = rt.base_rate * rate_multiplier(t) * ch.rate_factor * spend
                    rate *= r.uniform(0.93, 1.07)
                    if lead <= 3:
                        rate *= 1.06
                    cancelled_at = None
                    if cancelled:
                        gap = lead
                        cancel_day = booked_day + (r.randint(0, gap - 1) if gap > 0 else 0) * DAY
                        cancelled_at = datetime.combine(cancel_day, datetime.min.time()) + (
                            timedelta(minutes=r.randint(0, 1439))
                        )
                        if cancelled_at <= booked_at:
                            cancelled_at = booked_at + timedelta(minutes=r.randint(10, 180))
                        # a cancellation can happen on the arrival day, never after it
                        last_moment = datetime.combine(t, datetime.max.time()).replace(
                            microsecond=0
                        )
                        if cancelled_at > last_moment:
                            cancelled_at = booked_at + timedelta(seconds=30)
                    seq += 1
                    res_no = f"RSV{t:%y%m%d}{p.id}{seq:03d}"
                    b = Booking(res_no, p.id, rt.id, ch.id, gid, t, nights, adults, children,
                                round(rate), booked_at, cancelled_at)  # fmt: skip
                    if ch.type == "OTA":
                        b.ota_ref = f"{ch.code}-{stable_int('ota', res_no):09d}"
                        b.ota_link_missing = rng("ota-link", res_no).random() < 0.02
                    bookings.append(b)

    # warm-up stays that end before reporting starts are not part of the business history
    bookings = [b for b in bookings if b.check_out > REPORT_START]
    used = {b.guest_id for b in bookings}
    return [g for g in guests if g.id in used], bookings


def _simulate_audit(bookings: list[Booking]) -> dict[tuple[date, int], AuditDay]:
    sold: dict[tuple[date, int], int] = defaultdict(int)
    revenue: dict[tuple[date, int], int] = defaultdict(int)
    for b in bookings:
        if b.is_cancelled:
            continue
        for k in range(b.nights):
            d = b.check_in + k * DAY
            sold[d, b.property_id] += 1
            revenue[d, b.property_id] += b.rate

    audit = {}
    d = REPORT_START
    while d <= HORIZON:
        for p in PROPERTIES:
            r = rng("audit", d, p.id)
            room = revenue[d, p.id]
            fnb_ratio = p.fnb_ratio * r.uniform(0.88, 1.12)
            if p.id == 1 and d >= UBUD_ROOFTOP_OPENING:
                fnb_ratio *= 1.22
            audit[d, p.id] = AuditDay(
                d, p.id, rooms_available(p.id, d), sold[d, p.id], room,
                round(room * fnb_ratio), round(room * p.spa_ratio * r.uniform(0.8, 1.2)),
                round(room * r.uniform(0.02, 0.05)),
            )  # fmt: skip
        d += DAY
    return audit


def _review_score(r: random.Random, x: float) -> float:
    return round(max(1.0, min(5.0, x + r.gauss(0, 0.35))), 1)


def _simulate_reviews(bookings: list[Booking], country_of: dict[int, str]) -> list[Review]:
    reviews = []
    for b in bookings:
        if b.is_cancelled:
            continue
        r = rng("review", b.res_no)
        if r.random() > 0.42:
            continue
        p, ch = PROP[b.property_id], CH[b.channel_id]
        submitted = datetime.combine(b.check_out + r.randint(0, 6) * DAY, datetime.min.time())
        submitted += timedelta(minutes=r.randint(420, 1380))
        adj = 0.0
        if b.property_id == 2 and (
            SEMINYAK_CLEANLINESS_DIP[0] <= b.check_out <= SEMINYAK_CLEANLINESS_DIP[1]
        ):
            adj = -0.55
        if b.property_id == 2 and renovating(b.check_in):
            adj = -0.3
        direct = 0.08 if ch.type == "Direct" else 0
        clean = _review_score(r, p.rating + adj + direct)
        service = _review_score(r, p.rating + 0.05 + direct + adj * 0.3)
        location = _review_score(r, p.rating + 0.15)
        value = _review_score(r, p.rating - 0.15 + direct)
        overall = (clean + service + location + value) / 4 + r.gauss(0, 0.1)
        overall = round(max(1.0, min(5.0, overall)), 1)
        bucket = 5 if overall >= 4.6 else 4 if overall >= 3.8 else 3 if overall >= 3.0 else 2
        text = r.choice(REVIEW_TEXTS[bucket])
        if bucket <= 3 and adj < 0 and r.random() < 0.6:
            text = r.choice([REVIEW_TEXTS[2][0], REVIEW_TEXTS[3][0]])
        if ch.code == "BDC" and r.random() < 0.7:
            platform = "Booking.com"
        else:
            platform = pick_weighted(
                r, {"Google Reviews": 40, "TripAdvisor": 30, "Post-stay Survey": 30}
            )
        prefix = {"Booking.com": "BDC", "Google Reviews": "GGL", "TripAdvisor": "TA",
                  "Post-stay Survey": "SRV"}[platform]  # fmt: skip
        reviews.append(
            Review(
                f"{prefix}-{stable_int('review-id', b.res_no, digits=10):010d}",
                platform,
                b.property_id,
                b.res_no,
                submitted,
                {
                    "overall": overall,
                    "cleanliness": clean,
                    "service": service,
                    "location": location,
                    "value": value,
                },
                text,
                country_of[b.guest_id],
            )  # fmt: skip
        )
    return reviews


def _simulate_targets(
    audit: dict[tuple[date, int], AuditDay],
) -> dict[tuple[int, int, int], tuple[int, float]]:
    actual: dict[tuple[int, int, int], list[int]] = defaultdict(lambda: [0, 0, 0])
    for a in audit.values():
        acc = actual[a.audit_date.year, a.audit_date.month, a.property_id]
        acc[0] += a.room_revenue + a.fnb_revenue + a.spa_revenue + a.other_revenue
        acc[1] += a.rooms_sold
        acc[2] += a.rooms_available

    growth = {2026: {1: 1.10, 2: 1.10, 3: 1.12, 4: 1.08, 5: 1.10}, 2027: dict.fromkeys(PROP, 1.08)}
    targets = {}
    for p in PROPERTIES:
        for year in (2025, 2026, 2027):
            for month in range(1, 13):
                r = rng("target", year, month, p.id)
                if year == 2025:
                    rev, sold, avail = actual[2025, month, p.id]
                    rev_t = round(rev * r.uniform(0.96, 1.05) / 100) * 100
                    occ_t = round(sold / avail * r.uniform(0.97, 1.03), 3)
                else:
                    rev, sold, avail = actual[year - 1, month, p.id]
                    rev_t = round(rev * growth[year][p.id] / 100) * 100
                    occ_t = round(min(0.95, sold / avail * 1.03), 3)
                targets[year, month, p.id] = (rev_t, occ_t)
    return targets


@lru_cache(maxsize=1)
def build_world() -> World:
    guests, bookings = _simulate_bookings()
    country_of = {g.id: g.country for g in guests}
    reviews = _simulate_reviews(bookings, country_of)
    audit = _simulate_audit(bookings)
    world = World(guests, bookings, reviews, audit, _simulate_targets(audit))

    for b in bookings:
        world._by_booked_date.setdefault(b.booked_at.date(), []).append(b)
        if b.cancelled_at:
            world._by_cancel_date.setdefault(b.cancelled_at.date(), []).append(b)
    for rv in reviews:
        world._reviews_by_date.setdefault(rv.submitted_at.date(), []).append(rv)
    return world


def booked_on(world: World, d: date) -> list[Booking]:
    return sorted(world._by_booked_date.get(d, []), key=lambda b: b.booked_at)


def cancelled_on(world: World, d: date) -> list[Booking]:
    return sorted(world._by_cancel_date.get(d, []), key=lambda b: b.cancelled_at)


def booked_until(world: World, d: date) -> list[Booking]:
    return sorted((b for b in world.bookings if b.booked_at.date() <= d), key=lambda b: b.booked_at)


def reviews_on(world: World, d: date) -> list[Review]:
    return sorted(world._reviews_by_date.get(d, []), key=lambda rv: rv.submitted_at)


# kept for the docs: channel order matters for weights
assert [c.id for c in CHANNELS] == list(range(1, 11))
assert math.isclose(sum(channel_weights(SIM_START).values()), 1.0)
