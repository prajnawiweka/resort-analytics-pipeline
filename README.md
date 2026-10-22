# Resort Analytics Pipeline

[![CI](https://github.com/prajnawiweka/resort-analytics-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/prajnawiweka/resort-analytics-pipeline/actions/workflows/ci.yml)

Pipeline analitik end-to-end untuk **Tropical Haven Resort Group** (5 resort di Bali, data dummy): data harian dari beberapa sistem sumber dimuat ke PostgreSQL dengan Python, diolah dan dites dengan dbt, dijalankan otomatis oleh GitHub Actions, lalu ditampilkan di Looker Studio.

> **Status:** M1 Ingestion selesai: 4 sistem sumber, ±95 ribu baris riwayat dimuat ke skema `raw`. Lihat [Roadmap](#roadmap).

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
make pipeline END=2026-10-21   # buat tabel, file sumber s.d. END, muat ke raw
make ci                   # lint, test, cek koneksi dbt
```

| Perintah | Fungsi |
|---|---|
| `make up` / `make down` | Menyalakan / mematikan Postgres lokal |
| `make db-init` | Membuat skema `raw`, `staging`, `marts` dan tabel raw |
| `make generate END=YYYY-MM-DD` | Menulis file sumber untuk setiap tanggal bisnis s.d. END (default: kemarin) |
| `make load` | Memuat file baru atau berubah ke skema `raw` (file yang sama dilewati) |
| `make pipeline` | `db-init` + `generate` + `load` |
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
| M1 Ingestion | Generator multi-sumber, loader incremental, `load_log` | Selesai |
| M2 Modeling | Seed master data, model dbt staging dan marts, revenue vs target | Berikutnya |
| M3 Testing | Tes dbt dan rekonsiliasi | |
| M4 Automation | Pipeline harian ke Neon | |
| M5 Dashboard | Salinan dashboard Looker Studio membaca marts | |
| M6 Dokumentasi | README final, data dictionary, runbook, insight | |

## Data

Semua data adalah data dummy yang dibuat oleh generator di repo ini. Tidak ada data tamu atau bisnis sungguhan.

| Sistem sumber | File harian | Yang membuatnya "sulit" |
|---|---|---|
| PMS | `pms_reservations.csv`, `pms_night_audit.csv` | Kode hotel, tanggal `dd/mm/yyyy`, baris dobel, angka sebagai teks |
| Channel manager | `ota_bookings.json` | Nama properti dan ejaan channel sendiri, waktu UTC, link reservasi kadang hilang |
| Agregator review | `reviews.json` | Skala 1–10 dan 1–5, sub-skor tidak selalu ada, referensi booking berbeda |
| Finance | `finance_targets_<tahun>.xlsx` | Baris judul, bulan melebar ke samping, baris TOTAL |

Data juga ditanami pola bisnis yang harus muncul di dashboard: renovasi Seminyak (Feb 2026), penurunan kebersihan Seminyak (Jun–Sep 2026), kenaikan F&B Ubud setelah rooftop dibuka (Jun 2026), dan kampanye direct booking (Jan–Apr 2026). Kontrak lengkap setiap sumber ada di [docs/sources.md](docs/sources.md).
