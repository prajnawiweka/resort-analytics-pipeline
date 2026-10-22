# Catatan Keputusan

Setiap keputusan teknis penting dicatat di sini: pilihannya, alternatif yang dipertimbangkan, dan alasannya. Entri baru ditambahkan di bawah; entri lama tidak dihapus, hanya ditandai *diganti oleh #N* bila keputusannya berubah.

---

## 1. PostgreSQL sebagai database, bukan BigQuery

**Tanggal:** 22 Okt 2026

**Pilihan:** PostgreSQL.
**Alternatif:** Google BigQuery, tetap di Google Sheets.

**Alasan:** Data project ini kecil (±100 ribu baris), jadi kekuatan BigQuery untuk data skala besar tidak terpakai. PostgreSQL memungkinkan desain database relasional yang lengkap (primary key, foreign key, constraint) sehingga kualitas data dijaga oleh database itu sendiri. SQL PostgreSQL juga paling umum dipakai di industri dan bisa dijalankan gratis, baik lokal (Docker) maupun di cloud. Google Sheets tidak punya kunci, tipe data, atau validasi, sehingga tidak layak jadi sumber data tepercaya.

---

## 2. Neon sebagai hosting PostgreSQL, bukan Supabase

**Tanggal:** 22 Okt 2026

**Pilihan:** Neon (free tier).
**Alternatif:** Supabase, server sendiri (VPS), Aiven.

**Alasan:** Looker Studio hanya bisa membaca database yang bisa diakses dari internet, jadi Postgres harus di-hosting. Neon gratis, menyediakan koneksi IPv4 langsung yang bisa dipakai Looker Studio, dan tidak mem-pause project karena tidak aktif. Koneksi langsung Supabase saat ini hanya IPv6 sehingga harus lewat pooler, dan project gratisnya di-pause setelah 7 hari tanpa aktivitas. VPS menambah biaya dan pekerjaan administrasi server yang bukan fokus project BI.

---

## 3. dbt Core untuk transformasi dan tes

**Tanggal:** 22 Okt 2026

**Pilihan:** dbt Core (`dbt-postgres`).
**Alternatif:** script SQL biasa yang dijalankan Python, transformasi di pandas, calculated field di Looker Studio.

**Alasan:** dbt membuat setiap transformasi berupa file SQL yang punya urutan jelas (lineage), bisa dites (unique, not null, relasi, aturan bisnis), dan terdokumentasi otomatis. Definisi KPI cukup ditulis sekali dan dipakai semua dashboard. Script SQL biasa tidak punya tes dan lineage; pandas memindahkan logika bisnis ke luar database; calculated field di dashboard tidak bisa dites dan harus diulang di setiap laporan. dbt juga skill yang banyak diminta untuk posisi Data Analyst dan Analytics Engineer.

---

## 4. GitHub Actions untuk orkestrasi

**Tanggal:** 22 Okt 2026

**Pilihan:** GitHub Actions (CI untuk setiap PR dan pipeline terjadwal harian).
**Alternatif:** Apache Airflow, Dagster, cron di server sendiri.

**Alasan:** Pipeline ini hanya punya beberapa langkah berurutan sekali sehari, jadi orkestrator penuh seperti Airflow atau Dagster berlebihan dan butuh server yang terus menyala. GitHub Actions gratis untuk repo public, menyatu dengan kode, dan log setiap run tersimpan otomatis sebagai bukti pipeline berjalan. Kalau kebutuhan bertambah (banyak pipeline, ketergantungan antar-job), Dagster jadi kandidat pengganti.

---

## 5. Looker Studio sebagai dashboard utama, Power BI sebagai pelengkap

**Tanggal:** 22 Okt 2026

**Pilihan:** Looker Studio untuk dashboard publik; Power BI Desktop sebagai pelengkap opsional.
**Alternatif:** Tableau Public, Metabase, Apache Superset.

**Alasan:** Looker Studio gratis, bisa terhubung langsung ke PostgreSQL, dan bisa dibagikan lewat link sehingga reviewer langsung bisa membukanya. Power BI Desktop juga gratis dan bisa konek ke PostgreSQL, tetapi publish ke web butuh lisensi Pro; karena banyak lowongan di Indonesia mensyaratkan Power BI, file `.pbix` dan screenshot-nya disertakan sebagai pelengkap. Tableau Public tidak bisa konek ke database. Metabase dan Superset harus di-hosting sendiri.

---

## 6. Dashboard versi Google Sheets tetap dipertahankan

**Tanggal:** 22 Okt 2026

**Pilihan:** Dashboard lama (sumber Google Sheets) tetap ada; dashboard baru adalah salinan yang membaca tabel mart di PostgreSQL.
**Alternatif:** Langsung mengganti sumber data dashboard lama.

**Alasan:** Dengan dua versi berdampingan, angka hasil pipeline bisa direkonsiliasi dengan angka yang sudah diketahui benar untuk periode yang sama. Selisih nol menjadi bukti bahwa migrasi tidak mengubah hasil. Dashboard lama juga tetap berfungsi bila pipeline bermasalah selama masa transisi.

---

## 7. Skema raw tidak pernah diubah; semua transformasi di dbt

**Tanggal:** 22 Okt 2026

**Pilihan:** Data dimuat ke skema `raw` persis seperti diterima dari sumber. Pembersihan dan key mapping (misalnya kode properti `SMY` dan nama "TH Seminyak" menjadi `property_id` 2) dilakukan di lapisan `staging` oleh dbt.
**Alternatif:** Membersihkan dan memetakan data di script load sebelum masuk database.

**Alasan:** Raw adalah arsip asli. Bila aturan mapping ternyata salah atau berubah, cukup perbaiki SQL lalu bangun ulang `staging` dan `marts` dari raw, tanpa harus meminta ulang data ke sumber. Raw yang utuh juga memungkinkan audit ("sumber mengirim X, pipeline mengubahnya menjadi Y"). Selain itu, semua aturan bisnis terkumpul di satu tempat (dbt) dan bisa dites, tidak tersebar di script Python.

---

## 8. Empat sistem sumber dengan format berbeda, bukan satu file rapi

**Tanggal:** 22 Okt 2026

**Pilihan:** Generator meniru empat sistem: PMS (CSV), channel manager OTA (JSON), agregator review (JSON), dan Finance (Excel). Masing-masing memakai kode properti, ejaan channel, format tanggal, zona waktu, dan skala rating sendiri, plus data kotor yang disengaja (baris dobel, email huruf besar, spasi berlebih, link reservasi yang hilang).
**Alternatif:** Satu generator yang langsung menghasilkan tabel bersih sesuai skema akhir.

**Alasan:** Tanpa perbedaan antar sumber, tidak ada pekerjaan integrasi data: staging kosong dan tes tidak pernah menangkap apa pun. Di dunia nyata, PMS, channel manager, dan platform review memang tidak saling kenal. Meniru kondisi itu membuat project ini menunjukkan keterampilan inti BI: key mapping, conformed dimension, penanganan zona waktu, dan validasi kualitas data. Detail tiap sumber ada di [sources.md](sources.md).

---

## 9. Raw menyimpan teks dan jsonb apa adanya; reload per file dengan delete + insert

**Tanggal:** 22 Okt 2026

**Pilihan:** Kolom feed CSV disimpan sebagai `text`; feed JSON dan Excel disimpan sebagai satu record `jsonb` per item atau baris. Setiap file dimuat dalam satu transaksi: baris lama dari file itu dihapus, lalu semua baris dimasukkan ulang. File yang isinya (sha256) sudah pernah sukses dimuat dilewati. Setiap percobaan dicatat di `raw.load_log`.
**Alternatif:** Tabel raw bertipe ketat dengan primary key bisnis dan `INSERT ... ON CONFLICT DO UPDATE` (rencana awal di PRD).

**Alasan:** Tipe ketat di raw membuat satu nilai kotor (mis. `"12,345.00"`) menggagalkan seluruh load, padahal raw harus bisa menerima apa pun yang dikirim sumber. Upsert berdasarkan kunci bisnis juga akan menimpa versi lama dan membuang baris dobel, padahal keduanya bukti apa yang sebenarnya dikirim sumber. Dengan delete + insert per file, menjalankan ulang tanggal yang sama tidak pernah menggandakan data, dan versi terbaru per kunci dipilih di staging dengan aturan yang bisa dites. Header CSV yang berubah menghentikan load dan tercatat sebagai `failed`, sehingga perubahan format sumber selalu ketahuan.

---

## 10. Dunia simulasi deterministik; file harian adalah potret per tanggal bisnis

**Tanggal:** 22 Okt 2026

**Pilihan:** Simulator membangun seluruh "dunia" (Des 2024 – Des 2027) sekali, dengan angka acak yang ditentukan oleh kunci (tanggal menginap, tipe kamar, nomor reservasi). File untuk tanggal D hanya berisi apa yang diketahui sistem pada akhir hari D.
**Alternatif:** Generator yang menyimpan state dan menambah data hari demi hari; atau satu aliran angka acak global seperti generator versi Google Sheets.

**Alasan:** Pipeline harian di GitHub Actions tidak punya state antar-run, jadi file tanggal D harus selalu bisa dibuat ulang persis sama. Dengan kunci acak per entitas, menambah hari baru tidak mengubah riwayat. Konsekuensinya, angka versi baru tidak sama persis dengan data Google Sheets lama (lihat #11).

---

## 11. Data Google Sheets disamakan dengan data pipeline untuk pembanding

**Tanggal:** 22 Okt 2026

**Pilihan:** Di M5, riwayat dari pipeline baru diekspor sekali ke Google Sheets, sehingga dashboard versi Sheet dan versi PostgreSQL membaca data yang sama.
**Alternatif:** Membandingkan dengan data Sheet lama apa adanya; atau membuat generator baru meniru persis angka acak generator lama.

**Alasan:** Keputusan #6 butuh data yang identik supaya selisih nol bisa membuktikan pipeline benar. Generator lama memakai satu aliran angka acak global yang tidak bisa diperpanjang tanpa mengubah riwayat (lihat #10), jadi meniru angkanya tidak sebanding dengan manfaatnya. Ekspor satu kali ke Sheet lebih sederhana dan tetap memenuhi tujuan rekonsiliasi.

---

## 12. Master data sebagai dbt seed

**Tanggal:** 22 Okt 2026

**Pilihan:** Daftar properti, tipe kamar, channel, negara, dan tabel pemetaan kode antar sistem disimpan sebagai file CSV di `dbt/seeds/` (dikerjakan di M2).
**Alternatif:** Tabel master yang diisi manual di database; atau master data dari salah satu sistem sumber.

**Alasan:** Master data jarang berubah dan perlu ditinjau manusia. Sebagai seed, setiap perubahan (misalnya properti baru atau ejaan channel baru dari OTA) tercatat di Git lewat PR dan langsung dites bersama model lain. Tidak ada satu sistem sumber yang memegang semua kode, jadi pemetaan memang harus dibuat dan dirawat sendiri.

---

## 13. Booking OTA tanpa nomor reservasi dicocokkan lewat atribut menginap

**Tanggal:** 22 Okt 2026

**Pilihan:** Booking OTA dihubungkan ke reservasi PMS lewat `hotel_reservation_no`. Bila nomor itu kosong (±2% record), dicocokkan lewat kombinasi properti, channel, tanggal check-in, tanggal check-out, dan total harga, tetapi hanya jika tepat satu reservasi PMS yang belum terhubung cocok. Hasilnya dicatat di kolom `ota_match_method`.
**Alternatif:** Membuang record tanpa nomor reservasi; atau mencocokkan dengan aturan longgar (mis. hanya properti dan tanggal).

**Alasan:** Membuang record berarti komisi aktual hilang dan review Booking.com tidak bisa dihubungkan ke tamunya. Aturan longgar berisiko memasangkan booking ke reservasi yang salah, dan kesalahan seperti itu tidak terlihat di dashboard. Syarat "tepat satu kandidat" membuat pencocokan aman; record yang tetap tidak cocok muncul sebagai peringatan di tes dbt. Pada data riwayat, ke-535 record tanpa nomor berhasil dicocokkan.

---

## 14. KPI didefinisikan di mart; tabel fakta hanya berisi angka yang bisa dijumlahkan

**Tanggal:** 22 Okt 2026

**Pilihan:** `mart_property_monthly` menghitung semua KPI bulanan (occupancy, ADR, RevPAR, cancellation rate, direct booking share, rating, YoY) dari total bulanan. `fact_daily_revenue` dan `fact_bookings` hanya berisi kolom aditif; rasio untuk rentang tanggal bebas di dashboard dihitung sebagai SUM(pembilang) / SUM(penyebut).
**Alternatif:** Menyimpan rasio harian di tabel fakta; atau membiarkan semua KPI dihitung di calculated field Looker Studio seperti versi lama.

**Alasan:** Rata-rata dari rasio harian memberi angka yang salah (hari sepi dan hari ramai diberi bobot sama). Dengan kolom aditif, dashboard bisa memfilter tanggal dan properti apa pun lalu tetap menghitung rasio yang benar. Mart bulanan menjadi satu definisi resmi yang terdokumentasi dan dites, sehingga angka di dashboard, Power BI, maupun analisis lain selalu sama.

---

## 15. Identitas tamu = email (di-hash), segmen tamu dihitung dari riwayat

**Tanggal:** 22 Okt 2026

**Pilihan:** Tamu dikenali dari email yang sudah di-lowercase, lalu di-hash md5 sebagai `guest_key`. Segmen (New, Returning, VIP) dihitung dari jumlah menginap dan total belanja di semua reservasi.
**Alternatif:** Nama tamu sebagai kunci; atau nomor tamu dari PMS.

**Alasan:** PMS simulasi tidak mengirim nomor tamu, dan nama tidak unik. Email cukup stabil, tetapi kadang terkirim dalam huruf besar, sehingga harus dinormalisasi dulu. Hash membuat tabel mart tidak perlu menyimpan email, jadi dashboard tidak pernah menampilkan data pribadi.
