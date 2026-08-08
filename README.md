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

## ☁️ Panduan Deployment ke Render.com (Free Tier)

Aplikasi ini sudah dilengkapi dengan `Dockerfile` dan `render.yaml` sehingga siap dideploy ke **Render.com Free Tier** sebagai **Background Worker**.

### Langkah 1: Push Kode ke Repository GitHub
1. Buat repository baru di GitHub (misal: `telegram-assignment-bot`).
2. Jalankan perintah git di terminal proyek lokal Anda:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Render deployment"
   git branch -M main
   git remote add origin https://github.com/USERNAME/telegram-assignment-bot.git
   git push -u origin main
   ```

### Langkah 2: Deploy di Render.com
1. Buka [Render Dashboard](https://dashboard.render.com/) dan login.
2. Klik tombol **New +** -> pilih **Background Worker**.
3. Hubungkan ke repository GitHub Anda (`telegram-assignment-bot`).
4. Isikan konfigurasi berikut:
   - **Name:** `telegram-assignment-bot`
   - **Environment:** `Docker` *(akan otomatis terdeteksi via Dockerfile)*
   - **Region:** Singapore / Oregon / Frankfurt
   - **Branch:** `main`
   - **Plan:** `Free`
5. Pada bagian **Environment Variables**, tambahkan:
   - `TELEGRAM_BOT_TOKEN`: *(Isikan Token Telegram Bot dari @BotFather)*
   - `DEFAULT_NAMA`: *(Opsional, contoh: Nama Anda)*
   - `DEFAULT_NIM`: *(Opsional, contoh: NIM Anda)*
6. Klik **Create Background Worker**.

Render akan otomatis mendownload Dockerfile, menginstall **LibreOffice** untuk konversi PDF, menginstall dependensi Python, dan menjalankan bot Telegram 24/7 secara gratis!

---

## 💻 Penggunaan Lokal (Windows)

Jika ingin menjalankan secara lokal di PC:
```powershell
py main.py
```
atau klik 2x file **`run.bat`**.
