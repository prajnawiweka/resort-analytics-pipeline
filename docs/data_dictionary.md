# Data Dictionary

Tabel di skema `marts`, yaitu satu-satunya skema yang bisa dibaca dashboard (`looker_ro`). Semua uang dalam **USD**, semua tanggal dalam waktu Bali (WITA). Rasio disimpan sebagai pecahan (0,7660 = 76,60%).

Sumber kebenaran untuk definisi ini adalah SQL di `dbt/models/marts/` dan tes di `_marts.yml`. Bila keduanya berubah, file ini ikut diperbarui. `make dbt-docs` menampilkan lineage lengkap sampai ke tabel `raw`.

Aturan umum:

- **Grain** = satu baris mewakili apa. Kolom kunci grain dites unik oleh dbt.
- Kolom bertanda **aditif** boleh dijumlahkan lintas baris. Kolom rasio dan rata-rata **tidak**: gabungkan ulang dari kolom aditif (`SUM(pembilang) / SUM(penyebut)`), lihat keputusan #14 dan #18.
- Reservasi batal tetap ada di `fact_bookings`, tetapi revenue, malam kamar, dan komisinya 0.

---

## Fakta

### `fact_daily_revenue`

Night audit PMS. **Grain:** 1 properti × 1 hari (`date_day`, `property_id`).

| Kolom | Arti |
|---|---|
| `date_day` | Tanggal bisnis (night audit) |
| `property_id` | → `dim_property` |
| `rooms_available` | Kamar yang bisa dijual malam itu. Aditif |
| `rooms_sold` | Kamar terjual malam itu. Aditif |
| `room_revenue` | Revenue kamar. Aditif |
| `fnb_revenue`, `spa_revenue`, `other_revenue` | Revenue F&B, spa, lainnya. Aditif |
| `ancillary_revenue` | `fnb_revenue + spa_revenue + other_revenue`. Aditif |
| `total_revenue` | `room_revenue + ancillary_revenue`. Aditif |

### `fact_bookings`

Reservasi dari PMS, dilengkapi data OTA. **Grain:** 1 reservasi (`res_no`).

| Kolom | Arti |
|---|---|
| `res_no` | Nomor reservasi PMS |
| `property_id`, `room_type_id`, `channel_id`, `guest_key` | → dimensi terkait |
| `booked_at`, `booking_date` | Waktu dan tanggal booking |
| `check_in_date`, `check_out_date` | Tanggal menginap |
| `cancelled_at`, `cancellation_date` | Waktu dan tanggal batal; kosong bila tidak batal |
| `nights`, `adults`, `children` | Lama menginap dan jumlah tamu sesuai reservasi |
| `room_rate`, `total_amount` | Tarif per malam dan nilai reservasi, termasuk yang batal |
| `is_cancelled` | Reservasi batal |
| `booking_status` | `Cancelled`, `Completed` (check-out ≤ `data_as_of`), `In-house`, `Upcoming` |
| `lead_time_days` | Hari antara booking dan check-in; tidak pernah negatif |
| `room_nights` | Malam kamar; 0 bila batal. Aditif |
| `booking_revenue` | Nilai reservasi; 0 bila batal. Aditif |
| `commission_amount` | Komisi OTA; 0 bila batal atau direct. Aditif |
| `commission_source` | `ota_report` (angka aktual dari channel manager), `contract_rate` (tarif kontrak × nilai), `none` (direct) |
| `net_revenue` | `booking_revenue - commission_amount`. Aditif |
| `ota_ref` | Nomor booking di OTA, bila cocok |
| `ota_match_method` | Cara mencocokkan OTA ↔ PMS: `reservation_no`, `stay_attributes`, atau kosong untuk non-OTA (keputusan #13) |
| `is_repeat_guest` | Tamu sudah pernah menginap (tidak batal) sebelum reservasi ini |

### `fact_reviews`

Review dari semua platform. **Grain:** 1 review (`review_id`).

| Kolom | Arti |
|---|---|
| `review_id` | Id review |
| `property_id` | → `dim_property` |
| `review_date`, `submitted_at` | Tanggal dan waktu review |
| `platform` | `Post-stay Survey`, `Booking.com`, `Google Reviews`, `TripAdvisor` |
| `res_no`, `channel_id` | Reservasi terkait; hanya terisi untuk Post-stay Survey dan Booking.com |
| `reviewer_country_code` | Negara reviewer; dari reservasi bila platform tidak mengirimnya |
| `overall_rating`, `cleanliness_rating`, `service_rating`, `location_rating`, `value_rating` | Skor 1–5 (Booking.com 1–10 diubah ke 1–5). Google Reviews dan TripAdvisor hanya punya `overall_rating`; skor lain kosong |
| `is_low_rating` | `overall_rating < 4` (variabel dbt `low_rating_threshold`) |
| `review_text` | Isi review |

### `fact_monthly_target`

Target Finance. **Grain:** 1 properti × 1 bulan (`month_start`, `property_id`).

| Kolom | Arti |
|---|---|
| `month_start` | Tanggal 1 bulan target |
| `property_id` | → `dim_property` |
| `revenue_target` | Target total revenue sebulan penuh. Aditif |
| `occupancy_target` | Target occupancy (pecahan) |

---

## Dimensi

| Tabel | Grain | Kolom |
|---|---|---|
| `dim_property` | 1 resort | `property_id`, `property_code`, `property_name`, `location`, `total_rooms`, `property_type`, `opening_date` |
| `dim_room_type` | 1 tipe kamar per properti | `room_type_id`, `property_id`, `room_type_code`, `room_category`, `base_rate`, `max_occupancy`, `room_count` |
| `dim_channel` | 1 channel | `channel_id`, `channel_code`, `channel_name`, `channel_type` (`Direct`, `OTA`, `Paid`, `Social`, `Agent`), `commission_rate`, `is_direct` |
| `dim_guest` | 1 tamu | `guest_key` (md5 email huruf kecil; email sendiri tidak disimpan), `first_name`, `last_name`, `country_code`, `country_name`, `first_booking_date`, `stays`, `lifetime_spend`, `guest_segment` |
| `dim_date` | 1 hari, 1 Des 2024 – 31 Des 2027 | `date_day`, `year`, `quarter`, `month`, `month_name`, `month_start`, `day_of_week` (1 = Senin), `day_name`, `is_weekend_night` (Jumat/Sabtu), `season` |

- `guest_segment`: `VIP` = 3+ menginap atau belanja ≥ USD 6.000; `Returning` = 2 menginap; `New` = lainnya. Hanya reservasi tidak batal yang dihitung.
- `season`: `High` = Jul–Agu dan 20 Des–5 Jan; `Low` = Feb, Mar, Nov; `Shoulder` = lainnya.

---

## Mart KPI

### `mart_property_monthly`

Tabel KPI utama dashboard. **Grain:** 1 properti × 1 bulan (`month_start`, `property_id`).

Basis bulan berbeda per kelompok: KPI menginap memakai tanggal menginap, KPI booking memakai bulan **check-in**, KPI review memakai bulan review.

| Kolom | Arti |
|---|---|
| `month_start`, `property_id` | Kunci |
| `rooms_available`, `rooms_sold`, `room_revenue`, `ancillary_revenue`, `total_revenue` | Total sebulan dari `fact_daily_revenue`. Aditif |
| `occupancy_rate` | `rooms_sold / rooms_available` |
| `adr` | `room_revenue / rooms_sold` |
| `revpar` | `room_revenue / rooms_available` |
| `bookings`, `cancellations` | Reservasi dan reservasi batal (bulan check-in). Aditif |
| `cancellation_rate` | `cancellations / bookings` |
| `direct_booking_share` | Reservasi direct tidak batal / reservasi tidak batal |
| `avg_lead_time_days` | Rata-rata lead time |
| `commission_cost` | Total komisi. Aditif |
| `reviews` | Jumlah review. Aditif |
| `avg_rating`, `avg_cleanliness`, `avg_service` | Rata-rata skor review (1–5); gabungkan dengan bobot `reviews`. `avg_cleanliness` dan `avg_service` hanya dari platform yang mengirim skor rinci, sedangkan bobot `reviews` menghitung semua review, jadi gabungan lintas bulan untuk keduanya adalah pendekatan |
| `low_rating_share` | Review dengan rating < 4 / semua review |
| `total_revenue_last_year` | `total_revenue` bulan yang sama tahun lalu; kosong untuk semua bulan 2025 (night audit pertama 1 Jan 2025) |
| `total_revenue_yoy` | `total_revenue / total_revenue_last_year - 1` |
| `occupancy_rate_last_year` | Occupancy bulan yang sama tahun lalu |

Bulan berjalan berisi data sampai `data_as_of`, sedangkan kolom `_last_year` berisi bulan penuh. YoY bulan berjalan karena itu tampak lebih rendah.

### `mart_revenue_vs_target`

Aktual vs target. **Grain:** 1 properti × 1 bulan, sampai bulan `data_as_of`.

| Kolom | Arti |
|---|---|
| `month_start`, `property_id` | Kunci |
| `days_in_month`, `days_reported` | Hari dalam bulan dan hari yang sudah punya night audit |
| `is_month_complete` | `days_reported = days_in_month` |
| `actual_revenue` | Total revenue aktual. Aditif |
| `revenue_target` | Target sebulan penuh. Aditif |
| `revenue_target_to_date` | `revenue_target × days_reported / days_in_month` (prorata untuk bulan berjalan). Aditif |
| `revenue_achievement` | `actual_revenue / revenue_target_to_date` |
| `occupancy_actual`, `occupancy_target` | Occupancy aktual dan target |
| `occupancy_gap` | `occupancy_actual - occupancy_target` (poin pecahan) |

### `data_freshness`

**Grain:** 1 baris.

| Kolom | Arti |
|---|---|
| `data_as_of` | Tanggal bisnis terakhir yang punya night audit lengkap; ditampilkan dashboard sebagai "data per" |
| `last_loaded_at` | Waktu load sukses terakhir di `raw.load_log` |
