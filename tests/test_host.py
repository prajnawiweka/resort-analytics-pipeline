"""Host secrets pasted in common wrong shapes still resolve to the host name."""

import pytest

from ingestion.host import describe, normalize_host

HOST = "ep-cool-name-a1b2c3d4.ap-southeast-1.aws.neon.tech"


@pytest.mark.parametrize(
    "raw",
    [
        HOST,
        f"  {HOST}\n",
        f"postgresql://pipeline_rw:secret@{HOST}/resort?sslmode=require",
        f"postgres://pipeline_rw:secret@{HOST}:5432/resort",
        f"pipeline_rw:secret@{HOST}/resort",
        f"{HOST}/resort",
        f'"{HOST}"',
    ],
)
def test_normalize_host(raw):
    assert normalize_host(raw) == HOST


def test_describe_never_contains_the_value():
    facts = describe(f"postgresql://u:secret@{HOST}/resort")
    assert HOST not in str(facts) and "secret" not in str(facts)
    assert facts["has_scheme"] and facts["ends_with_neon_tech"]
