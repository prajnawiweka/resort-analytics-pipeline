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
