# Resort Analytics Pipeline

[![CI](https://github.com/prajnawiweka/resort-analytics-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/prajnawiweka/resort-analytics-pipeline/actions/workflows/ci.yml)

Pipeline analitik end-to-end untuk **Tropical Haven Resort Group** (5 resort di Bali, data dummy): data harian dari beberapa sistem sumber dimuat ke PostgreSQL dengan Python, diolah dan dites dengan dbt, dijalankan otomatis oleh GitHub Actions, lalu ditampilkan di Looker Studio.

> **Status:** M0 Setup selesai. Lihat [Roadmap](#roadmap).

## Masalah yang diselesaikan

Dashboard versi sebelumnya membaca Google Sheets yang diisi dengan copy-paste: tanpa kunci, tanpa validasi, dan rumus KPI tersebar di calculated field dashboard. Project ini menggantinya dengan satu sumber data tepercaya, definisi KPI tunggal di SQL, tes kualitas data otomatis, dan update harian tanpa campur tangan manual.

## Arsitektur

```
Sistem sumber        Ingestion          PostgreSQL (Neon)                  BI
(PMS, OTA,     ──▶   generate.py  ──▶   raw ──▶ staging ──▶ marts   ──▶   Looker Studio
 review, finance)    load.py                  └──── dbt ────┘              (Power BI opsional)

                     └──────────── dijalankan oleh GitHub Actions ────────────┘
```

| Lapisan | Isi | Dibangun oleh |
|---|---|---|
| `raw` | Data persis seperti diterima dari sumber, tidak pernah diubah | `ingestion/load.py` |
| `staging` | Tipe data rapi, nilai seragam, kode sumber dipetakan ke kunci bersama | dbt |
| `marts` | Star schema (fact & dimension) dan KPI untuk dashboard | dbt |

Alasan setiap pilihan teknologi ada di [docs/decisions.md](docs/decisions.md).

## Menjalankan secara lokal

Prasyarat: Python 3.12+, Docker.

```bash
cp .env.example .env      # isi password lokal
make install              # dependency Python + dbt
make up                   # PostgreSQL 16 di Docker
make ci                   # buat skema, lint, test, cek koneksi dbt
```

| Perintah | Fungsi |
|---|---|
| `make up` / `make down` | Menyalakan / mematikan Postgres lokal |
| `make db-init` | Membuat skema `raw`, `staging`, `marts` |
| `make lint` | Cek gaya kode Python (ruff) |
| `make test` | Unit test Python (butuh database menyala) |
| `make dbt-debug` | Cek dbt bisa terhubung ke database |

## Struktur repo

```
ingestion/            Python: koneksi DB, generator data, loader
sql/                  DDL skema, dijalankan berurutan oleh make db-init
dbt/                  Project dbt: models/staging, models/marts, tests, seeds
tests/                Unit test Python
data/incoming/        File harian hasil generator (tidak di-commit)
docs/                 Catatan keputusan, data dictionary, runbook
.github/workflows/    CI dan pipeline harian
```

## Roadmap

| Fase | Isi | Status |
|---|---|---|
| M0 Setup | Struktur repo, Postgres lokal, CI | Selesai |
| M1 Ingestion | Generator multi-sumber, loader incremental, `load_log` | Berikutnya |
| M2 Modeling | Model dbt staging dan marts, revenue vs target | |
| M3 Testing | Tes dbt dan rekonsiliasi | |
| M4 Automation | Pipeline harian ke Neon | |
| M5 Dashboard | Salinan dashboard Looker Studio membaca marts | |
| M6 Dokumentasi | README final, data dictionary, runbook, insight | |

## Data

Semua data adalah data dummy yang dibuat oleh generator di repo ini. Tidak ada data tamu atau bisnis sungguhan.
