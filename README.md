# Telegram Assignment Converter Bot

Bot Telegram berbasis Python untuk otomatisasi konversi foto tugas tulisan tangan menjadi dokumen Microsoft Word (`.docx`) dan file `PDF` yang rapi dan siap diunggah ke e-learning kampus.

## 🚀 Fitur Utama
1. **Pilihan Mode Gambar:**
   - 📷 **Foto Asli / Normal:** Menjaga warna & pencahayaan asli foto.
   - ⚡ **Efek Scanner (BETA):** Mengubah latar belakang menjadi putih seperti scanner.
2. **Otomatisasi Dokumen Word (.docx):**
   - Mengisi data identitas (Nama, NIM, Mata Kuliah, Tanggal) pada template Word.
   - Skala proporsional otomatis agar Gambar 1 pas duduk di Halaman 1 bawah header.
3. **Pilihan Format & Tombol Ambil Pintas:**
   - Pilihan output PDF, DOCX, atau Keduanya.
   - Tombol pintas untuk mengambil format alternatif jika salah pencet.
4. **Keamanan & Pembersihan:**
   - Sanitasi nama file output `[NIM]_[Nama]_[MataKuliah]_[JudulTugas].pdf`.
   - Pembersihan otomatis file sementara di folder `temp/`.

---

## ☁️ Panduan Deployment ke Render.com (Free Tier - Web Service)

Layanan Background Worker di Render memang berbayar, tetapi **Web Service di Render memiliki paket GRATIS (Free Tier $0/month)**.

Aplikasi ini sudah dilengkapi dengan server HTTP internal ringan pada `main.py` sehingga dapat dideploy secara 100% **GRATIS** sebagai **Web Service** di Render.com!

### Langkah Deployment di Render.com:
1. Buka [Render Dashboard](https://dashboard.render.com/).
2. Klik tombol **New +** -> pilih **Web Service** (Bukan Background Worker).
3. Hubungkan ke repository GitHub Anda (`fhriads/bot-tugas`).
4. Isikan konfigurasi berikut:
   - **Name:** `bot-tugas`
   - **Environment:** `Docker`
   - **Region:** Singapore / Oregon / Frankfurt
   - **Branch:** `main`
   - **Instance Type:** `Free` ($0/month)
5. Pada bagian **Environment Variables**, tambahkan:
   - `TELEGRAM_BOT_TOKEN`: *(Token Telegram Bot dari @BotFather)*
6. Klik **Create Web Service**.

Render akan mem-build Docker container, menginstall **LibreOffice** untuk konversi PDF, dan menjalankan bot Telegram 24/7 secara GRATIS!

---

## 💻 Penggunaan Lokal (Windows)

Jika ingin menjalankan secara lokal di PC:
```powershell
py main.py
```
atau klik 2x file **`run.bat`**.
