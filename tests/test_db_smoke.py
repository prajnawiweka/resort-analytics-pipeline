"""Smoke test: the database is reachable and the three layers exist."""

from ingestion.db import connect

EXPECTED_SCHEMAS = {"raw", "staging", "marts"}


def test_can_connect():
    with connect() as conn:
        assert conn.execute("select 1").fetchone() == (1,)


def test_layer_schemas_exist():
    with connect() as conn:
        rows = conn.execute(
            "select schema_name from information_schema.schemata where schema_name = any(%s)",
            (list(EXPECTED_SCHEMAS),),
        ).fetchall()
    assert {r[0] for r in rows} == EXPECTED_SCHEMAS
