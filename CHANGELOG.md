# Changelog

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id-ID/1.1.0/). Versi mengikuti milestone project.

## [0.5.0] - 2026-10-22 · M4 Automation (menunggu Neon)

### Ditambahkan
- Workflow `daily_pipeline.yml`: jadwal 06:17 WITA dan tombol manual; init, generate, load, dbt build, cek kesegaran, ringkasan run, arsip hasil dbt. Melewati diri sendiri dengan aman selama secret Neon belum diisi.
- `generate --catch-up`: mengejar setiap tanggal bisnis sejak load terakhir sampai kemarin (waktu Bali).
- `ingestion/check_freshness.py`: gagal bila `data_as_of` belum mencapai kemarin.
- `sql/roles/neon_setup.sql`: skema milik `pipeline_rw`, `looker_ro` hanya bisa membaca `marts`.
- `docs/runbook.md`: setup Neon, secret GitHub, koneksi Looker Studio, penanganan run gagal.
- 5 tes Python untuk logika tanggal dan catch-up; keputusan #16–#17.

## [0.4.0] - 2026-10-22 · M3 Testing

### Ditambahkan
- 4 tes rekonsiliasi dbt: night audit vs reservasi, mart bulanan vs fakta harian, tidak ada reservasi hilang dari raw, night audit lengkap setiap hari.
- 6 tes aturan bisnis dbt: kapasitas kamar, urutan waktu reservasi, tidak ada data setelah `data_as_of`, komisi OTA vs kontrak, target tersedia untuk setiap bulan, peringatan load terakhir gagal.
- `docs/testing.md`: strategi tiga lapis tes dan bukti tes gagal saat data dirusak lalu pulih dengan `--force`.

## [0.3.0] - 2026-10-22 · M2 Modeling

### Ditambahkan
- Seed master data di skema `reference`: properti, tipe kamar, channel, negara, pemetaan nama properti dan ejaan channel antar sistem.
- Model staging untuk 5 feed: cast tipe, versi terbaru per kunci, konversi UTC → WITA, skala rating 1–5, unpivot target Finance tanpa baris TOTAL.
- Model intermediate: id perusahaan untuk reservasi PMS; pencocokan OTA ↔ PMS lewat nomor reservasi atau atribut menginap.
- Star schema di `marts`: 4 tabel fakta, 5 dimensi, `mart_property_monthly` (definisi KPI), `mart_revenue_vs_target`, `data_freshness`.
- 99 node dbt (model, seed, tes) dan 7 tes Python baru (seed vs sistem sumber, file deterministik).
- CI menjalankan pipeline 2 bulan data + `dbt build`.
- Keputusan #13–#15.

### Diperbaiki
- File Excel Finance kini identik byte demi byte saat digenerate ulang, sehingga loader tidak memuatnya ulang tanpa alasan.

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
