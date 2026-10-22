"""Clean up the database host setting and describe it without revealing it.

People often paste a whole connection string (postgresql://user:pw@host/db?sslmode=require)
or stray spaces into the host secret. normalize_host() keeps only the host name.

    python -m ingestion.host   # in CI: report the shape and export the cleaned host
"""

from __future__ import annotations

import os
import socket
import sys
from urllib.parse import urlsplit


def normalize_host(raw: str) -> str:
    value = raw.strip().strip('"').strip("'").strip()
    if "://" in value:
        value = urlsplit(value).hostname or ""
    elif "@" in value or "/" in value:
        value = urlsplit("//" + value).hostname or ""
    return value.strip()


def describe(raw: str) -> dict[str, object]:
    """Facts about the value that help debugging but never reveal it."""
    clean = normalize_host(raw)
    return {
        "length": len(raw),
        "has_whitespace": raw != raw.strip() or any(c.isspace() for c in raw.strip()),
        "has_scheme": "://" in raw,
        "has_at_sign": "@" in raw,
        "has_slash": "/" in raw,
        "is_pooler_host": "-pooler" in clean,
        "ends_with_neon_tech": clean.endswith(".neon.tech"),
        "cleaned_length": len(clean),
    }


def address_counts(host: str) -> dict[str, int]:
    """How many IPv4 and IPv6 addresses the host resolves to (no addresses are printed)."""
    counts = {}
    for name, family in (("ipv4_addresses", socket.AF_INET), ("ipv6_addresses", socket.AF_INET6)):
        try:
            counts[name] = len({a[4][0] for a in socket.getaddrinfo(host, 5432, family)})
        except socket.gaierror:
            counts[name] = 0
    return counts


def main() -> int:
    raw = os.getenv("POSTGRES_HOST", "")
    clean = normalize_host(raw)
    facts = {**describe(raw), **(address_counts(clean) if clean else {})}
    for key, value in facts.items():
        print(f"{key}: {value}")
    if os.getenv("GITHUB_ACTIONS"):
        print("::notice title=database host::" + ", ".join(f"{k}={v}" for k, v in facts.items()))
    if not clean:
        print("::error title=host::POSTGRES_HOST is empty after cleaning")
        return 1
    github_env = os.getenv("GITHUB_ENV")
    if github_env:
        print(f"::add-mask::{clean}")
        with open(github_env, "a") as f:
            f.write(f"POSTGRES_HOST={clean}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
