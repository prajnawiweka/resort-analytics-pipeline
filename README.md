# Resort Analytics Pipeline

[![CI](https://github.com/prajnawiweka/resort-analytics-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/prajnawiweka/resort-analytics-pipeline/actions/workflows/ci.yml)

Pipeline analitik end-to-end untuk **Tropical Haven Resort Group** (5 resort di Bali, data dummy): data harian dari beberapa sistem sumber dimuat ke PostgreSQL dengan Python, diolah dan dites dengan dbt, dijalankan otomatis oleh GitHub Actions, lalu ditampilkan di Looker Studio.

> **Status:** M4 Automation siap: workflow harian, catch-up otomatis, dan cek kesegaran data sudah dites lokal. Menunggu database Neon untuk run pertama. Lihat [Roadmap](#roadmap).

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

Alasan setiap pilihan teknologi ada di [docs/decisions.md](docs/decisions.md). Setup Neon, operasi harian, dan penanganan gagal ada di [docs/runbook.md](docs/runbook.md).

## Model data (skema `marts`)

| Tabel | Grain | Isi |
|---|---|---|
| `fact_bookings` | 1 reservasi | Tanggal booking/check-in, status, lead time, revenue, komisi, tamu berulang |
| `fact_daily_revenue` | 1 properti × 1 hari | Kamar tersedia/terjual, revenue kamar, F&B, spa, lainnya |
| `fact_reviews` | 1 review | Rating skala 1–5, platform, negara reviewer, reservasi terkait bila ada |
| `fact_monthly_target` | 1 properti × 1 bulan | Target revenue dan occupancy dari Finance |
| `dim_property`, `dim_room_type`, `dim_channel`, `dim_guest`, `dim_date` | — | Dimensi; `dim_guest` tanpa email (kunci di-hash) |
| `mart_property_monthly` | 1 properti × 1 bulan | **Semua KPI dashboard** + perbandingan tahun lalu |
| `mart_revenue_vs_target` | 1 properti × 1 bulan | Aktual vs target, target bulan berjalan di-prorata |
| `data_freshness` | 1 baris | Tanggal data terakhir (`data_as_of`) |

| KPI | Definisi |
|---|---|
| Occupancy | kamar terjual ÷ kamar tersedia |
| ADR | revenue kamar ÷ kamar terjual |
| RevPAR | revenue kamar ÷ kamar tersedia |
| Cancellation rate | reservasi batal ÷ semua reservasi (bulan check-in) |
| Direct booking share | reservasi direct tidak batal ÷ reservasi tidak batal |
| Low rating share | review dengan rating < 4 ÷ semua review |

Lapisan dbt: `staging` (bersihkan, ketik, pilih versi terbaru) → `intermediate` (petakan kode sumber ke id perusahaan, cocokkan OTA ↔ PMS) → `marts`.

## Bagaimana angka dijamin benar

Tiga lapis tes berjalan di setiap PR dan setiap run harian: tes Python untuk kode, tes struktur dbt (kunci, relasi, nilai), dan tes rekonsiliasi (misalnya night audit harus sama dengan reservasi yang menginap). Bila satu tes gagal, model turunannya tidak dibangun, sehingga angka yang salah tidak sampai ke dashboard. Detail dan bukti percobaan ada di [docs/testing.md](docs/testing.md).

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
| `make pipeline` | `db-init` + `generate` + `load` + `dbt-build` |
| `make dbt-build` | Memuat seed, membangun staging dan marts, menjalankan semua tes dbt |
| `make dbt-docs` | Dokumentasi dbt dan lineage graph di browser |
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
| M2 Modeling | Seed master data, model dbt staging dan marts, revenue vs target | Selesai |
| M3 Testing | Tes rekonsiliasi dan aturan bisnis lanjutan | Selesai |
| M4 Automation | Pipeline harian ke Neon | Siap; menunggu setup Neon |
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
