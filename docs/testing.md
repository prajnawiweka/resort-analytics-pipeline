# Strategi Pengujian

Angka di dashboard hanya boleh terbit bila tiga lapis pengujian lulus. Setiap lapis menangkap jenis kesalahan yang berbeda.

| Lapis | Alat | Jumlah | Menangkap | Dijalankan |
|---|---|---|---|---|
| 1. Kode Python | pytest (`tests/`) | 29 | Bug di generator dan loader: aturan bisnis simulasi, isi file per tanggal, idempotensi load, seed vs sistem sumber | Setiap PR (CI) |
| 2. Struktur data | dbt generic tests (`_*.yml`) | 74 | Kunci dobel atau kosong, relasi putus, nilai di luar daftar, kode sumber yang belum dipetakan | Setiap `dbt build` |
| 3. Kebenaran angka | dbt singular tests (`dbt/tests/`) | 10 | Angka yang tidak saling cocok antar tabel atau antar sistem, aturan bisnis yang dilanggar | Setiap `dbt build` |

`dbt build` menjalankan model dan tesnya berurutan: bila tes sebuah model gagal, model turunannya dilewati (`SKIP`), sehingga data yang salah tidak mengalir ke mart dan dashboard.

## Tes rekonsiliasi dan aturan bisnis

| Tes | Aturan | Arti bila gagal |
|---|---|---|
| `assert_night_audit_matches_reservations` | Kamar terjual dan revenue kamar di night audit = reservasi tidak batal yang menginap malam itu | Reservasi hilang, dobel, atau salah tanggal |
| `assert_monthly_mart_matches_daily_fact` | Total mart KPI bulanan = total fakta harian per properti | Logika agregasi mart salah |
| `assert_no_reservation_lost_from_raw` | Setiap `RES_NO` di raw sampai ke `fact_bookings` | Kode hotel, kamar, atau channel baru belum ada di seed |
| `assert_audit_days_complete` | Ada night audit untuk setiap properti setiap hari sampai `data_as_of` | File harian tidak terkirim atau gagal dimuat |
| `assert_rooms_sold_within_capacity` | Kamar terjual ≤ tersedia ≤ total kamar | Data PMS tidak masuk akal |
| `assert_booking_timeline_valid` | Booking ≤ check-in; pembatalan setelah booking dan paling lambat hari check-in | Urutan waktu reservasi rusak |
| `assert_no_data_after_as_of_date` | Tidak ada booking, review, atau audit bertanggal setelah `data_as_of` | Data masa depan bocor ke laporan |
| `assert_ota_commission_matches_contract` | Komisi dari OTA = tarif kontrak × total (toleransi USD 1) | Tarif di seed salah atau tagihan OTA keliru |
| `assert_targets_cover_reported_months` | Setiap bulan yang punya data aktual punya target Finance | Grafik revenue vs target bolong |
| `assert_latest_load_of_each_file_succeeded` | Percobaan load terakhir setiap file sukses (**warn**) | Format sumber berubah; perlu dicek manusia |

## Bukti: tes gagal saat data dirusak

Pada 22 Okt 2026, data raw tanggal 2026-06-09 sengaja dirusak dengan tiga cara, lalu `dbt build` dijalankan:

| Kerusakan | Tes yang gagal | Akibat |
|---|---|---|
| Satu baris `pms_reservations` dihapus (data hilang di perjalanan) | `assert_night_audit_matches_reservations` (1 baris) | `mart_property_monthly` dan tesnya dilewati |
| Ejaan channel baru dari OTA: `"Booking.com Partner"` | `not_null_stg_ota__bookings_channel_id` (1 baris) | Model turunan OTA dilewati |
| Night audit melaporkan 99 kamar terjual dari 78 tersedia | `assert_rooms_sold_within_capacity` (1 baris) | Mart KPI tidak dibangun |

Pemulihan: `python -m ingestion.load --date 2026-06-09 --force` memuat ulang empat file asli dari sumber, lalu `dbt build` kembali lulus 109/109. Karena raw selalu bisa dibangun ulang dari file sumber, perbaikan tidak membutuhkan edit manual di database.

Catatan dari percobaan: kerusakan pada record OTA yang punya versi lebih baru tidak berdampak, karena staging memakai versi terbaru. Itu perilaku yang diharapkan, bukan celah tes.

## Menjalankan

```bash
make test        # pytest (butuh database)
make dbt-build   # seed + model + semua tes dbt
cd dbt && dbt test --select test_type:singular --profiles-dir .   # hanya rekonsiliasi
```
