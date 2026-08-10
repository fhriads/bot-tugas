# 🌸 Ringkasan Perkembangan Proyek Bot Telegram "Gwis" (Session Summary)

Dokumen ini mencatat seluruh arsitektur, fitur yang telah diimplementasikan, perbaikan bug, dan panduan untuk sesi pengembangan AI selanjutnya agar **tidak kehilangan konteks**.

---

## 📌 1. Identitas & Persona Bot
* **Nama Bot**: **Gwis** (Virtual Study Assistant Cewek yang Perhatian, Ramah, & Pintar 🌸).
* **Aturan Penting Persona (Strict Rule)**:
  - **JANGAN PERNAH** menyebutkan kata *"Gemini AI"* atau *"AI"* pada pesan balasan bot kepada pengguna.
  - Seluruh kecerdasan ekstraksi dan pemrosesan diatribusikan sepenuhnya sebagai kemampuan **Gwis** (misal: *"Gwis lagi mencatat deadline kamu... ✨"*).
  - Bahasa balasan ramah, penyayang, membantu, dengan emotikon khas `🌸 ✨ 📚 ⏰ 📅`.

---

## 🛠️ 2. Tech Stack & Dependensi Utama
* **Bahasa**: Python 3.10+
* **Framework Bot**: `python-telegram-bot>=20.0`
* **AI Engine**: `google-genai>=0.1.0` (Official Google GenAI SDK terbaru).
  - Model aktif yang digunakan secara berurutan: `gemini-2.0-flash`, `gemini-2.5-flash-lite`, `gemini-flash-latest`.
* **Pengolah Dokumen**: `python-docx`, `PyMuPDF` (`fitz`), `Pillow`, `OpenCV` (`opencv-python-headless`).
* **Isolasi Multi-User**:
  - Profil pengguna: `config/profiles.json` (terisolasi per Telegram `user_id`).
  - Deadline pengguna: `config/deadlines.json` (terisolasi per Telegram `user_id`).
  - Jadwal kuliah: `config/schedules.json` (terisolasi per Telegram `user_id`).

---

## 🚀 3. Fitur yang Telah Selesai Diimplementasikan & Aktif

### 📚 A. Buat Tugas Baru (`/tugas`)
* Konversi foto tugas tulisan tangan ke template dokumen Word (`.docx`) dan PDF.
* Pilihan mode tampilan: **📷 Foto Asli (Normal)** vs **⚡ Efek Scanner (BETA)**.
* Konversi otomatis dan pengiriman file Word & PDF secara bersamaan / sesuai pilihan.

### 🔄 B. Convert PDF ke Word (`/convert`)
* Mengonversi dokumen PDF hasil scan (CamScanner / foto) ke file Word (`.docx`).
* Mempertahankan seluruh gambar tanpa ada halaman bertumpuk atau hilang.
* Menghitung tinggi maksimum gambar (`max_h <= 9.2 inch`) untuk mencegah bug halaman kosong (*blank pages*).

### ⏰ C. Pengingat Deadline Tugas (`/deadline`)
* **Input Bahasa Alami**: Pengguna bisa mengetik pesan santai (contoh: `"tugas kalkulus 2 kumpul besok jam 11 malam"`).
* **AI Draft Confirmation**: Menampilkan draf pratinjau dengan tombol `[ ✅ Simpan Deadline ]` dan `[ ❌ Batal ]`.
* **Notifikasi Latar Belakang Otomatis**:
  - H-1 (24 Jam sebelum deadline).
  - 3 Jam sebelum deadline.
  - Urgent Test (< 10 Menit sebelum deadline).
* **Tombol `[ ✅ Sudah Selesai ]`**:
  - Ada pada setiap pesan notifikasi pengingat dan di menu `/deadline`.
  - Tugas yang ditandai selesai (`completed: True`) tidak akan pernah menerima notifikasi pengingat lagi.
* **Filtering Otomatis**: Tugas yang sudah selesai atau yang sudah melewati waktu deadline otomatis dihilangkan dari daftar deadline aktif.

### 📅 D. Jadwal Kuliah & Ruangan (`/jadwal`)
* **OCR Foto / Screenshot / Teks**: Membaca foto tabel jadwal perkuliahan / KRS / foto papan dan mengekstraknya menjadi struktur jadwal mingguan harian.
* **AI Draft Confirmation**: Pratinjau draf jadwal dengan tombol `[ ✅ Simpan & Update Jadwal ]` dan `[ ❌ Batal ]`.
* **Tombol `🔄 Update / Edit Jadwal`**: Memungkinkan pengguna mengirim foto/teks jadwal baru untuk menimpa/memperbarui jadwal lama kapan saja.
* **Pintasan Cepat**: Tombol `📌 Jadwal Hari Ini` dan `🗓 Jadwal 1 Minggu`.

### 🔘 E. Persistent Telegram Bot Command Menu (`[/] Menu`)
* Menampilkan menu perintah resmi Telegram (`[/] Menu`) di sudut kiri bawah layar obrolan pengguna yang terdaftar via `set_my_commands`:
  - `/start` - 🌸 Menu Utama Gwis
  - `/tugas` - 📚 Buat Tugas Baru (Word/PDF)
  - `/convert` - 🔄 Convert PDF ke Word (.docx)
  - `/deadline` - ⏰ Pengingat Deadline Tugas
  - `/jadwal` - 📅 Jadwal Kuliah & Ruangan
  - `/profile` - 👤 Lihat Profil Pengguna
  - `/setup` - ✏️ Ubah Nama & NIM
  - `/cancel` - ❌ Batal / Keluar Sesi

---

## 🐛 4. Perbaikan Bug Penting yang Telah Diselesaikan
1. **Perbaikan Limit `callback_data` Telegram (64 Bytes Limit)**:
   - Penggunaan `context.user_data` untuk menyimpan path file daripada memasukkan string panjang ke `callback_data`.
2. **Dukungan HTTP Proxy PythonAnywhere Free Tier**:
   - `HTTPXRequest(proxy="http://proxy.server:3128")` dikonfigurasi otomatis saat terdeteksi lingkungan PythonAnywhere.
3. **Pemberantasan Halaman Kosong pada Konversi PDF**:
   - Penyesuaian `max_h = Inches(9.2)` dan `space_after = Pt(0)` pada `python-docx` untuk mencegah *soft page break* tambahan.
4. **Penyelesaian `RuntimeError: no running event loop`**:
   - Pendaftaran background scheduler dan menu perintah menggunakan `post_init` hook (`post_init_scheduler`) pada `ApplicationBuilder`.
5. **Migrasi `google-genai` SDK & Pembersihan Warning**:
   - Menggunakan SDK official `google-genai` pengganti paket lama `google.generativeai` yang sudah deprecated.

---

## 🗂️ 5. Struktur Berkas Proyek

```text
auto-assignment-bot/
├── main.py                   # Entry point bot, registrasi handler & post_init hook
├── requirements.txt          # Dependensi Python
├── .env                      # Token TELEGRAM_BOT_TOKEN & GEMINI_API_KEY
├── SESSION_SUMMARY.md        # Ringkasan konteks proyek untuk AI (file ini)
├── create_template.py        # Generator bawaan template Word (.docx)
├── src/
│   ├── ai_processor.py       # Pengolah Gemini (parser deadline & OCR jadwal dengan SDK google-genai)
│   ├── bot_handlers.py       # Seluruh callback & conversation handler Telegram (Persona Gwis)
│   ├── config_manager.py     # Pengelola konfigurasi & profil per user_id
│   ├── deadline_manager.py   # Pengelola penyimpanan & status deadline per user_id
│   ├── doc_generator.py      # Pengolah pembuat file Word dari gambar
│   ├── image_processor.py    # Pipeline pengolah gambar (Scanner effect & scaling)
│   ├── pdf_converter.py      # Converter PDF ke DOCX (PyMuPDF / LibreOffice)
│   ├── schedule_manager.py   # Pengelola penyimpanan & jadwal kuliah per user_id
│   └── scheduler_service.py  # Service notifikasi pengingat deadline di latar belakang
├── config/
│   ├── profiles.json         # Data profil pengguna per user_id
│   ├── deadlines.json        # Data deadline per user_id
│   └── schedules.json        # Data jadwal perkuliahan per user_id
├── templates/                # Folder simpan template Word
└── output/                   # Folder hasil output file .docx & .pdf
```

---

## 💡 6. Ide Pengembangan Selanjutnya (Top Recommendations)
1. **`💬 Draf Template Chat Sopan ke Dosen` (Etika WA Dosen)**: Template pesan WA etis untuk izin sakit, bimbingan, atau konfirmasi revisi.
2. **`📊 Perekap Kehadiran & Jatah Bolos Kuliah` (Attendance Tracker)**: Melacak sisa kuota bolos agar tidak kena sanksi larangan ikut UAS (max 75% kehadiran).
3. **`🧮 Kalkulator Target Nilai UTS/UAS & IPK Simulator`**: Menghitung nilai minimal UTS/UAS yang harus diraih untuk mendapat Grade A/B+ dan menaikkan IPK.

---

*Dokumen ini dibuat pada: 10 Agustus 2026*
