# Runbook

Cara menyiapkan, menjalankan, dan memperbaiki pipeline. Bagian A dikerjakan sekali; bagian B–D untuk operasi harian.

## A. Setup pertama kali (sekitar 20 menit)

### A1. Database di Neon

1. Daftar di [neon.com](https://neon.com) (free plan cukup: 1 GB per project, compute tidur otomatis setelah 5 menit tanpa aktivitas; cek ulang di [halaman pricing](https://neon.com/pricing)).
2. **New project**: nama `resort-analytics`, region **AWS Asia Pacific (Singapore)** (terdekat dari Bali), Postgres 16, nama database `resort`.
3. Menu **SQL Editor**, pilih database `resort`, lalu salin seluruh isi [`sql/roles/neon_setup.sql`](../sql/roles/neon_setup.sql) ke editor.
4. Di editor, ganti dua password contoh (`REPLACE-pipeline-password`, `REPLACE-looker-password`) dengan password kuat (minimal 12 karakter, campuran huruf besar, kecil, angka, simbol). Simpan keduanya di password manager, jangan di chat atau file repo. Klik **Run**.
   - Script membuat role `pipeline_rw` dan `looker_ro` **lewat SQL**. Jangan membuatnya di menu **Roles**: role dari menu itu otomatis anggota `neon_superuser` sehingga bisa membaca semua data ([dokumentasi Neon](https://neon.com/docs/manage/database-access)).
   - Hasil akhir yang benar: dua baris, `pipeline_rw` dan `looker_ro`, keduanya `is_neon_superuser = false`.
5. Tombol **Connect** → matikan **Connection pooling** → catat host (tanpa `-pooler`). Pipeline memakai host langsung karena loader memakai `COPY` dalam transaksi panjang.

### A2. Secret di GitHub

Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Nama | Isi |
|---|---|
| `NEON_HOST` | Host langsung dari langkah A1.5, mis. `ep-xxxx.ap-southeast-1.aws.neon.tech` |
| `NEON_DATABASE` | `resort` |
| `NEON_USER` | `pipeline_rw` |
| `NEON_PASSWORD` | Password `pipeline_rw` |

Selama secret belum diisi, workflow harian tetap jalan tetapi langsung berhenti dengan pesan *"NEON_* secrets are not set yet"* (tidak dianggap gagal).

### A3. Run pertama (backfill)

**Actions → Daily pipeline → Run workflow**. Database masih kosong, jadi run ini membuat semua file sejak 2024-12-31 sampai kemarin dan memuatnya (beberapa menit). Selesai bila langkah *"Check the marts reach yesterday"* hijau.

### A4. Looker Studio

Mengikuti [panduan Neon untuk Looker Studio](https://neon.com/docs/connect/connect-looker-studio):

1. Unduh sertifikat CA [`isrgrootx1.pem`](https://letsencrypt.org/certs/isrgrootx1.pem).
2. Looker Studio → **Create → Data source → PostgreSQL**.
3. Host: host Neon (boleh yang `-pooler`), Port: kosong, Database: `resort`, Username: `looker_ro`, Password: password `looker_ro`.
4. Centang **Enable SSL**, jangan centang client authentication, unggah `isrgrootx1.pem` di **Server Certificate**.
5. **Authenticate** → pilih tabel dari skema `marts` (mis. `mart_property_monthly`, `fact_daily_revenue`).

## B. Operasi harian

| Kapan | Apa yang terjadi |
|---|---|
| 06:17 WITA | Workflow *Daily pipeline* jalan otomatis |
| | `generate --catch-up`: membuat file untuk setiap tanggal sejak load terakhir sampai kemarin (hari yang terlewat ikut dikejar) |
| | `load`: memuat file baru; file yang sudah ada dilewati |
| | `dbt build`: membangun ulang staging dan marts, menjalankan 84 tes |
| | `check_freshness`: gagal bila data belum sampai kemarin |
| Pagi | Cek badge atau email GitHub. Ringkasan run (tanggal data, file dan baris per sumber) ada di halaman run |

Tidak ada yang perlu dikerjakan bila run hijau.

## C. Bila run gagal

GitHub mengirim email ke pemilik repo. Buka run → langkah yang merah:

| Langkah merah | Penyebab umum | Tindakan |
|---|---|---|
| Install dependencies | Paket tidak bisa diunduh | Jalankan ulang (*Re-run jobs*) |
| Create schemas / Load | Secret salah, password diganti, compute Neon habis kuota | Cek secret dan dashboard Neon |
| Load: `FAILED ...: header ... does not match` | Sumber mengubah format kolom | Sesuaikan loader dan tabel raw lewat PR; jangan ubah data manual |
| dbt build: `not_null_stg_*_id` | Kode atau ejaan baru dari sumber (properti, channel) | Tambahkan ke seed pemetaan (`dbt/seeds/*_map.csv`) lewat PR |
| dbt build: `assert_*` | Angka tidak cocok antar tabel | Baca baris yang gagal: `dbt test --select <nama_tes> --store-failures`; lihat [testing.md](testing.md) |
| Check freshness | Run sebelumnya gagal atau terlewat | Perbaiki penyebabnya lalu *Run workflow*; `--catch-up` mengejar hari yang tertinggal |

Memuat ulang satu tanggal dari file sumber (mis. data raw rusak):

```bash
python -m ingestion.generate --date 2026-06-09
python -m ingestion.load --date 2026-06-09 --force
cd dbt && dbt build --profiles-dir .
```

## D. Perawatan

- **Jadwal berhenti sendiri:** GitHub menonaktifkan workflow terjadwal di repo public yang tidak ada aktivitas commit selama 60 hari. Bila itu terjadi: **Actions → Daily pipeline → Enable workflow**.
- **Batas simulasi:** dunia simulasi berakhir 31 Des 2027; generator menolak tanggal setelah **30 Jun 2027**. Sebelum itu, perpanjang `HORIZON` di `ingestion/config.py`.
- **Ganti password:** ubah di Neon, lalu perbarui secret `NEON_PASSWORD` (pipeline) atau kredensial data source Looker Studio (`looker_ro`).
- **Lokal:** `make up`, `make pipeline`, `make ci`; lihat README.
