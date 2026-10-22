"""dbt seeds (the company's master data) must agree with the systems that send data."""

import csv
from pathlib import Path

from ingestion.config import CHANNELS, COUNTRIES, PROPERTIES, ROOM_TYPES

SEEDS = Path(__file__).resolve().parent.parent / "dbt" / "seeds"


def read(name):
    with (SEEDS / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def test_property_codes_match_pms():
    seed = {r["property_code"]: int(r["total_rooms"]) for r in read("properties")}
    assert seed == {p.code: p.rooms for p in PROPERTIES}


def test_room_type_codes_match_pms():
    assert {r["room_type_code"] for r in read("room_types")} == {r.code for r in ROOM_TYPES}


def test_channel_codes_match_pms():
    assert {r["channel_code"] for r in read("channels")} == {c.code for c in CHANNELS}


def test_every_source_property_name_is_mapped():
    mapped = {(r["source_system"], r["source_name"]) for r in read("property_name_map")}
    for p in PROPERTIES:
        assert {("ota", p.ota_name), ("review", p.review_name), ("finance", p.name)} <= mapped


def test_every_ota_channel_spelling_is_mapped():
    mapped = {r["source_name_normalized"] for r in read("channel_name_map")}
    spellings = {s.strip().lower() for c in CHANNELS for s in c.ota_spellings}
    assert spellings <= mapped


def test_countries_cover_pms_codes():
    assert {r["country_code"] for r in read("countries")} == set(COUNTRIES)
