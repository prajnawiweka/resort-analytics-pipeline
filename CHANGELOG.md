# Changelog

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id-ID/1.1.0/). Versi mengikuti milestone project.

## [0.2.0] - 2026-10-22 · M1 Ingestion

### Ditambahkan
- Simulator deterministik (`ingestion/simulator.py`): reservasi, menginap, night audit, review, dan target Des 2024 – Des 2027, dengan pola bisnis yang ditanam.
- Generator file sumber per tanggal bisnis (`ingestion/generate.py`, `ingestion/sources.py`) untuk 4 sistem: PMS (CSV), channel manager (JSON), agregator review (JSON), Finance (Excel).
- Tabel landing `raw.*` dan `raw.load_log` (`sql/01_raw.sql`).
- Loader (`ingestion/load.py`): satu transaksi per file, lewati file yang tidak berubah (sha256), header CSV yang berubah tercatat `failed`.
- Target Makefile `generate`, `load`, `pipeline`.
- 20 tes baru: aturan bisnis simulator, isi file per tanggal, idempotensi loader.
- `docs/sources.md` (kontrak data) dan keputusan #8–#12.

### Diperbaiki
- Pembatalan yang jatuh setelah tanggal check-in untuk reservasi yang dibuat larut malam di hari kedatangan (ditemukan oleh tes).

## [0.1.0] - 2026-10-22 · M0 Setup

### Ditambahkan
- Struktur repo: `ingestion/`, `sql/`, `dbt/`, `tests/`, `docs/`.
- PostgreSQL 16 lokal lewat `docker-compose.yml`.
- Skema `raw`, `staging`, `marts` (`sql/00_init.sql`, `make db-init`).
- Helper koneksi database dari environment variable (`ingestion/db.py`).
- Project dbt dengan profile berbasis environment variable dan nama skema tanpa prefix.
- CI GitHub Actions dengan Postgres service container: lint, smoke test, `dbt debug`.
- Catatan keputusan awal (`docs/decisions.md`, 7 keputusan).
