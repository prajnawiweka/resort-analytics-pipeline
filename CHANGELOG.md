# Changelog

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id-ID/1.1.0/). Versi mengikuti milestone project.

## [0.1.0] - 2026-10-22 · M0 Setup

### Ditambahkan
- Struktur repo: `ingestion/`, `sql/`, `dbt/`, `tests/`, `docs/`.
- PostgreSQL 16 lokal lewat `docker-compose.yml`.
- Skema `raw`, `staging`, `marts` (`sql/00_init.sql`, `make db-init`).
- Helper koneksi database dari environment variable (`ingestion/db.py`).
- Project dbt dengan profile berbasis environment variable dan nama skema tanpa prefix.
- CI GitHub Actions dengan Postgres service container: lint, smoke test, `dbt debug`.
- Catatan keputusan awal (`docs/decisions.md`, 7 keputusan).
