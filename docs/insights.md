# Insight Bisnis · Jan–Sep 2026

Data per 21 Okt 2026, bulan lengkap Jan–Sep 2026. Semua angka dihitung dari skema `marts`; query ada di `dbt/analyses/` (jalankan `dbt compile`, lalu eksekusi file di `target/compiled/.../analyses/`).

> Data ini adalah simulasi dengan pola bisnis yang sengaja ditanam (lihat [sources.md](sources.md)). Yang ditunjukkan di sini adalah cara membaca data dan menurunkan tindakan, bukan kondisi resort sungguhan.

## Ringkasan

- Revenue grup Jan–Sep 2026 mencapai **98,5% dari target** (kurang USD 343 ribu). **Seminyak sendiri tertinggal USD 563 ribu (92,9%)**, lebih besar dari seluruh selisih grup.
- Penyebab utama Seminyak adalah **pertumbuhan yang lambat (+2,2% YoY, target +10%)**. Penurunan skor kebersihan Jun–Sep (4,28 → 3,81) adalah **risiko reputasi baru** yang perlu ditangani sebelum menekan permintaan.
- Kampanye direct booking berhasil: share direct naik **18,0% → 24,3%**, biaya komisi turun dari 11,9% ke 10,7% revenue (**hemat ±USD 200 ribu** untuk Jan–Sep).
- OTA punya cancellation rate **18,6%**, hampir tiga kali Direct (6,4%).
- Rooftop Ubud menaikkan F&B per kamar terisi **+29%** YoY (properti lain +4–6%).

## 1. Seminyak menanggung seluruh selisih target

| Properti | Aktual (USD) | Target (USD) | Selisih (USD) | Pencapaian | Pertumbuhan YoY |
|---|---|---|---|---|---|
| Seminyak | 7.378.540 | 7.941.200 | −562.660 | 92,9% | +2,2% |
| Canggu | 3.437.954 | 3.564.300 | −126.346 | 96,5% | +8,0% |
| Sanur | 4.042.663 | 4.144.400 | −101.737 | 97,5% | +5,4% |
| Ubud | 3.934.854 | 3.760.600 | +174.254 | 104,6% | +15,1% |
| Nusa Dua | 3.914.460 | 3.641.100 | +273.360 | 107,5% | +18,3% |

Seminyak di bawah target di 8 dari 9 bulan, termasuk sebelum masalah kebersihan muncul. Februari terendah (86,6%) karena renovasi menutup 10 Beachfront Suite: kamar tersedia turun 12,4% dan revenue −4,8% YoY.

**Tindakan:** Revenue Manager meninjau target Seminyak sisa tahun (asumsi +10% vs realisasi +2,2%) dan menyusun rencana akselerasi permintaan (paket, kampanye direct) khusus Seminyak.

## 2. Kebersihan Seminyak turun tajam pada Jun–Sep 2026

| Properti | Kebersihan Jan–May 2026 | Kebersihan Jun–Sep 2026 | Rating rendah Jun–Sep 2025 | Rating rendah Jun–Sep 2026 |
|---|---|---|---|---|
| Seminyak | 4,28 | **3,81** | 3,8% | **13,9%** |
| 4 properti lain | 4,40–4,70 | 4,43–4,66 | 0–0,7% | 0–1,3% |

Penurunan hanya terjadi di Seminyak dan hanya pada periode itu; properti lain stabil. Ulasan yang secara tertulis mengeluhkan kebersihan kamar masih sedikit, tetapi naik dari 2 ulasan (0,2%) pada Jun–Sep 2025 menjadi 14 ulasan (1,3%) pada Jun–Sep 2026. Skor angka bergerak lebih dulu daripada keluhan tertulis.

**Tindakan:** GM Seminyak dan Housekeeping mengaudit proses pembersihan kamar dan rasio staf per kamar musim ramai, lalu memantau skor kebersihan bulanan di halaman Guest Satisfaction sampai kembali ≥ 4,3.

## 3. Kampanye direct booking memangkas biaya komisi

| Menginap Jan–Sep | Share direct | Revenue booking (USD) | Biaya komisi (USD) | Komisi / revenue |
|---|---|---|---|---|
| 2025 | 18,0% | 15.172.417 | 1.805.579 | 11,9% |
| 2026 | **24,3%** | 16.394.492 | 1.751.494 | **10,7%** |

Revenue naik 8,1% sementara biaya komisi turun 3,0%. Selisih 1,2 poin persentase dari revenue 2026 setara **±USD 200 ribu** yang tidak dibayarkan ke perantara.

**Tindakan:** Marketing melanjutkan kampanye, dengan prioritas Seminyak (lihat temuan 1); ukur keberhasilan dengan share direct dan komisi/revenue di dashboard, bukan hanya jumlah booking.

## 4. Booking OTA paling sering batal

| Tipe channel | Booking (check-in Jan–Sep 2026) | Cancellation rate | Rata-rata lead time (hari) |
|---|---|---|---|
| OTA | 9.525 | **18,6%** | 30,0 |
| Paid | 1.102 | 11,6% | 29,7 |
| Social | 1.097 | 9,9% | 34,3 |
| Agent | 1.363 | 9,0% | 59,6 |
| Direct | 3.760 | **6,4%** | 39,1 |

Lead time OTA justru lebih pendek dari Direct, jadi tingginya pembatalan bukan karena booking dibuat terlalu jauh hari. Dugaan yang perlu dicek: kebijakan pembatalan gratis di OTA (data kebijakan tarif belum ada di pipeline).

**Tindakan:** Revenue Manager mengevaluasi tarif non-refundable di OTA dan overbooking terukur pada tanggal ramai untuk menutup kamar yang batal mendadak.

## 5. Rooftop Ubud menaikkan pendapatan F&B

| Properti | F&B per kamar terisi Jun–Sep 2025 (USD) | Jun–Sep 2026 (USD) | Perubahan |
|---|---|---|---|
| Ubud | 64,72 | **83,70** | **+29,3%** |
| Canggu | 93,98 | 99,23 | +5,6% |
| Nusa Dua | 92,31 | 97,49 | +5,6% |
| Sanur | 66,23 | 69,05 | +4,3% |
| Seminyak | 106,69 | 113,48 | +6,4% |

Hanya Ubud yang melonjak setelah rooftop dibuka Juni 2026; ini menjelaskan sebagian pertumbuhan YoY Ubud (+15,1%).

**Tindakan:** Manajemen F&B mengkaji apakah konsep serupa layak di Sanur, yang F&B per kamar terisinya terendah di 2026 (USD 69).

## Batasan

- Rating Google dan TripAdvisor tidak punya sub-skor; skor kebersihan berasal dari Booking.com dan Post-stay Survey.
- Pencapaian target bergantung pada asumsi target Finance; temuan 1 menunjukkan selisih, bukan penyebab tunggal.
- Penghematan komisi adalah selisih rasio dikali revenue, bukan hasil eksperimen terkontrol.
