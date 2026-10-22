# Kontrak Data Sumber

Pipeline menerima file dari empat sistem sumber. Setiap sistem memakai kode, nama, format tanggal, dan zona waktu sendiri; menyatukannya adalah tugas lapisan `staging` di dbt.

Semua data adalah simulasi (`ingestion/simulator.py`). File untuk satu tanggal bisnis ditulis ke `data/incoming/<YYYY-MM-DD>/` oleh `python -m ingestion.generate`, lalu dimuat ke skema `raw` oleh `python -m ingestion.load`.

## Ringkasan

| File | Sistem | Format | Tabel raw | Kapan dikirim |
|---|---|---|---|---|
| `pms_reservations.csv` | PMS (Property Management System) | CSV | `raw.pms_reservations` | Setiap hari |
| `pms_night_audit.csv` | PMS | CSV | `raw.pms_night_audit` | Setiap hari mulai 2025-01-01 |
| `ota_bookings.json` | Channel manager (OTA) | JSON | `raw.ota_bookings` | Setiap hari |
| `reviews.json` | Agregator review | JSON | `raw.reviews` | Setiap hari mulai 2025-01-01 |
| `finance_targets_<tahun>.xlsx` | Finance | Excel | `raw.finance_targets` | Saat target disetujui: 2024-12-31 (2025), 2025-12-15 (2026), 2026-12-15 (2027) |

Tanggal 2024-12-31 adalah ekspor pembuka: berisi **semua** reservasi yang sudah dibuat sampai hari itu.

## Kunci yang berbeda antar sistem

| Konsep | PMS | Channel manager | Review | Finance |
|---|---|---|---|---|
| Properti | Kode hotel `UBD`, `SMY`, `CGU`, `SNR`, `NSD` | `TH Ubud`, `TH Seminyak`, `Tropical Haven Canggu Surf`, `TH Sanur Family`, `TH Nusa Dua` | `Tropical Haven Resort - Ubud`, dst. | `Tropical Haven Ubud`, dst. |
| Channel | Kode `WEB`, `BDC`, `EXP`, `AGD`, `GADS`, `IG`, `TA`, `ABNB`, `TRIP`, `CORP` | Nama dengan ejaan beragam: `Booking.com`, `booking.com`, `BOOKING.COM`, `Booking.com ` | Nama platform | — |
| Reservasi | `RES_NO` (mis. `RSV2603105012`) | `ota_ref` (mis. `BDC-559370089`) + `hotel_reservation_no` = `RES_NO` | Booking.com: `ota_ref`; Post-stay Survey: `RES_NO`; Google & TripAdvisor: tidak ada | — |
| Negara | ISO alpha-2 (`AU`, `GB`) | — | Nama Inggris (`Australia`, `United Kingdom`) | — |
| Waktu | Lokal WITA (UTC+8) | UTC (`...Z`) | UTC (`...Z`) | — |

Akibat zona waktu: reservasi yang dibuat 21/10/2026 00:20 WITA tercatat `2026-10-20T16:20:00Z` di feed OTA. Tanggal bisnis selalu mengikuti waktu lokal.

## pms_reservations.csv

Satu baris per reservasi yang **dibuat atau dibatalkan** pada tanggal bisnis. Reservasi yang dibatalkan belakangan muncul lagi di file tanggal pembatalannya dengan `STATUS = CANCELLED`, jadi versi terbaru per `RES_NO` adalah yang dipakai.

| Kolom | Isi | Catatan |
|---|---|---|
| `RES_NO` | Nomor reservasi PMS | Kunci alami |
| `HOTEL_CODE` | Kode properti | |
| `ROOM_TYPE` | Kode tipe kamar, mis. `SMY-BFS` | |
| `ARRIVAL`, `DEPARTURE` | Tanggal `dd/mm/yyyy` | |
| `NIGHTS`, `ADULTS`, `CHILDREN` | Bilangan bulat | |
| `RATE`, `TOTAL` | USD per malam, USD total | |
| `STATUS` | `RESERVED` atau `CANCELLED` per akhir tanggal bisnis | Status `Completed` diturunkan dari tanggal |
| `SOURCE` | Kode channel | Kadang ada spasi di belakang |
| `GUEST_NAME` | `NAMA BELAKANG, Nama depan` | |
| `GUEST_EMAIL` | Email tamu | Kadang huruf besar semua; kunci tamu setelah `lower()` |
| `GUEST_COUNTRY` | ISO alpha-2 | |
| `CREATED_AT`, `CANCELLED_AT` | `dd/mm/yyyy HH:MM` WITA | `CANCELLED_AT` kosong bila tidak batal |

Kualitas data yang disengaja: sekitar 1% baris terkirim dua kali persis sama.

## pms_night_audit.csv

Satu baris per properti per tanggal: kamar tersedia, kamar terjual, dan pendapatan per departemen.

| Kolom | Isi | Catatan |
|---|---|---|
| `AUDIT_DATE` | `dd/mm/yyyy` | |
| `HOTEL_CODE` | Kode properti | |
| `ROOMS_AVAILABLE`, `ROOMS_SOLD` | Bilangan bulat | Kamar Seminyak berkurang 10 selama renovasi 2–28 Feb 2026 |
| `ROOM_REV`, `FB_REV`, `SPA_REV`, `OTHER_REV` | USD sebagai teks, mis. `"12,345.00"` | Hapus koma sebelum cast |

`ROOMS_SOLD` dan `ROOM_REV` selalu cocok dengan reservasi yang menginap malam itu; ini dasar tes rekonsiliasi.

## ota_bookings.json

```json
{"report_date": "2026-10-21", "property_group": "Tropical Haven", "bookings": [
  {"ota_ref": "EXP-360481873", "channel": "Expedia", "property": "TH Seminyak",
   "hotel_reservation_no": "RSV2611062014",
   "stay": {"check_in": "2026-11-06", "check_out": "2026-11-13"},
   "total_amount": 2968, "commission": {"amount": 534.24, "currency": "USD"},
   "status": "confirmed", "booked_at": "2026-10-20T16:20:00Z", "cancelled_at": null}]}
```

Hanya channel bertipe OTA (Booking.com, Expedia, Agoda, Airbnb, TripAdvisor). Komisi aktual hanya ada di sumber ini. Sekitar 2% record tidak membawa `hotel_reservation_no`.

## reviews.json

```json
[{"review_id": "SRV-2066130169", "platform": "Post-stay Survey",
  "property": "Tropical Haven Resort - Nusa Dua", "booking_reference": "RSV2610195007",
  "reviewer_country": null,
  "rating": {"scale": 5, "overall": 5.0, "cleanliness": 5.0, "service": 4.8, "location": 4.5, "value": 5.0},
  "text": "Stunning villa and flawless service. Will be back.", "submitted_at": "2026-10-20T23:42:00Z"}]
```

| Platform | Skala | Sub-skor | Referensi booking | Negara reviewer |
|---|---|---|---|---|
| Booking.com | 1–10 | Ada | `ota_ref` | Ada |
| Post-stay Survey | 1–5 | Ada | `RES_NO` | Kosong (ambil dari PMS) |
| Google Reviews | 1–5 | Tidak ada | Tidak ada | Ada |
| TripAdvisor | 1–5 | Tidak ada | Tidak ada | Ada |

Untuk Booking.com, review dihubungkan ke reservasi lewat dua langkah: `ota_ref` → `raw.ota_bookings` → `hotel_reservation_no`.

## finance_targets_&lt;tahun&gt;.xlsx

Dua sheet, `Revenue Target` (USD) dan `Occupancy Target` (pecahan, format persen). Baris 1–2 berisi judul dan catatan, header ada di baris 4 (`Property`, `Jan-26` … `Dec-26`), satu baris per properti dengan nama resmi. Sheet revenue diakhiri baris `TOTAL` berisi rumus `=SUM(...)` yang harus dibuang di staging.

Loader menyimpan setiap baris di bawah header sebagai satu record `jsonb` dengan kunci = judul kolom.

## Metadata di setiap tabel raw

| Kolom | Isi |
|---|---|
| `_load_id` | Merujuk `raw.load_log` |
| `_source_file` | `<tanggal bisnis>/<nama file>` |
| `_row_number` | Nomor baris/record dalam file (Excel: nomor baris spreadsheet) |
| `_loaded_at` | Waktu dimuat |
