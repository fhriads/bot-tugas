Product Requirement Document (PRD)
Local Assignment Document Automation Bot (Python + Telegram)
1. Document Control & Metadata
Project Name: Local Assignment Document Automation Bot (auto-assignment-bot)
Version: 1.0.0
Target Environment: Local Machine (Windows / macOS / Linux)
Primary Language: Python 3.10+
Target Audience/Users: Single User (Local Developer / Student)
Document Status: Ready for AI Agent Execution
2. Problem Statement & Objectives
2.1 Problem Statement
Mahasiswa sering menerima tugas kuliah tulisan tangan yang harus dikumpulkan melalui platform e-learning kampus. Alur manual saat ini membutuhkan banyak waktu dan tidak efisien:
Mengambil foto lembar jawaban menggunakan smartphone.
Memindahkan atau melakukan scanning satu per satu melalui aplikasi CamScanner.
Mengirim foto ke laptop.
Membuka Microsoft Word, menyusun tata letak (layout), mengisi data diri (Nama, NIM, Matkul, Tanggal).
Menempelkan foto ke dalam dokumen satu per satu secara manual.
Mengonversi Word ke PDF.
Mengubah nama file sesuai format penamaan tugas kampus.
2.2 Objective
Membangun bot Telegram lokal berbasis Python yang secara otomatis:
Menerima sekumpulan foto jawaban dari pengguna melalui Telegram.
Memproses foto secara otomatis (pemotongan/cropping, pencerahan, perataan kontras ala CamScanner).
Memasukkan data identitas tugas ke dalam template Microsoft Word (.docx).
Menempelkan foto yang telah diolah secara berurutan ke dalam template tersebut.
Mengonversi dokumen Word menjadi PDF.
Mengirimkan kembali file PDF final yang telah dinamai sesuai standar ke chat Telegram pengguna.
3. High-Level Architecture & Tech Stack
3.1 Architecture Overview
Aplikasi ini berjalan sebagai Local Service menggunakan teknik Polling Telegram Bot API. Seluruh pemrosesan file, pengolahan gambar, rendering dokumen, dan konversi PDF dilakukan secara lokal di perangkat pengguna.
+------------------+         +-------------------------------+
|  Telegram App    | <-----> | Local Python Service          |
|  (Mobile / Web)  |  HTTP   |  ├─ Telegram Listener (Bot)   |
+------------------+         |  ├─ Profile & State Manager   |
                             |  ├─ Image Processing (OpenCV) |
                             |  ├─ Docx Generator (docx)     |
                             |  └─ PDF Converter (docx2pdf)  |
                             +-------------------------------+


3.2 Technology Stack
Runtime: Python 3.10+
Bot Framework: python-telegram-bot (v20.x atau lebih baru, mengasumsikan pola async/await)
Image Processing: opencv-python, Pillow, numpy
Document Generation: python-docx
PDF Conversion: docx2pdf (Windows/macOS) atau LibreOffice CLI (Cross-platform)
Configuration & Environment: python-dotenv, pydantic / json untuk manajemen profil lokal.
4. User Workflow & Experience (UX)
4.1 Onboarding & Configuration Workflow
Inisialisasi Bot: Pengguna menjalankan bot di lokal (python main.py).
Setup Profil (/setup): Pengguna memasukkan data identitas bawaan melalui command Telegram:
Nama Lengkap
NIM (Nomor Induk Mahasiswa)
Program Studi / Kelas
Data tersimpan di file konfig lokal (config/profile.json).
4.2 Core Assignment Submission Workflow
Memulai Tugas (/tugas): Pengguna mengetik /tugas di Telegram.
Input Parameter Task: Bot meminta informasi spesifik tugas:
Nama Mata Kuliah
Judul / Pertemuan Tugas (contoh: "Tugas 02 - Matriks & Vektor")
Tanggal Pengumpulan (default: Hari Ini)
Pengiriman Foto: Pengguna mengirimkan 1 hingga  foto lembar jawaban tulisan tangan secara berurutan.
Trigger Proses (/selesai): Pengguna mengonfirmasi bahwa semua halaman telah dikirim.
Pemrosesan Otomatis: Bot menampilkan pesan status (Processing...):
Step 1/4: Filtering & Cropping Images.
Step 2/4: Generating Word Document.
Step 3/4: Converting to PDF.
Step 4/4: Uploading file.
Delivery: Bot mengirimkan file .pdf siap unggah beserta file .docx opsional ke chat pengguna.
5. Functional Requirements (Detailed Specifications)
FR-1: Telegram Bot Interface & Command System
FR-1.1: Bot harus mendukung perintah /start untuk menyapa pengguna dan menampilkan menu navigasi.
FR-1.2: Bot harus mendukung perintah /profile untuk melihat profil yang tersimpan saat ini.
FR-1.3: Bot harus mendukung perintah /setup untuk memperbarui profil (Nama, NIM, Kelas) menggunakan interaksi pesan bertahap (ConversationHandler).
FR-1.4: Bot harus mendukung perintah /cancel untuk membatalkan proses pengerjaan tugas yang sedang berlangsung.
FR-1.5: Bot harus mengimplementasikan state management yang jelas (WAITING_METADATA -> RECEIVING_IMAGES -> PROCESSING).
FR-2: Image Processing Engine (CamScanner Filter Replacement)
Modul pengolahan citra wajib menggunakan OpenCV dan Numpy dengan algoritma sebagai berikut:
FR-2.1 Auto Orientation: Mengoreksi orientasi foto berdasarkan metadata EXIF agar posisi halaman selalu tegak (portrait).
FR-2.2 Perspective Transform (Auto-Crop):
Mendeteksi kontur terbesar pada gambar (asumsi kertas tugas adalah segi empat terbesar pada latar belakang).
Melakukan Warp Perspective 4-titik untuk meluruskan gambar kertas jika difoto dari sudut miring.
Fallback Strategy: Jika kontur kertas tidak terdeteksi dengan tepat, gunakan seluruh area foto dengan memotong margin luar sebesar 2%.
FR-2.3 Image Enhancement (Scanner Effect):
Mengubah warna ke Grayscale atau menerapkan Adaptive Thresholding (Gaussian / Otsu) untuk memisahkan tulisan tangan dari latar belakang kertas.
Menerapkan koreksi Brightness dan Contrast agar latar belakang kertas menjadi putih bersih ( RGB value) dan tinta tulisan tangan terlihat tegas/hitam.
Menyimpan foto hasil pemrosesan ke folder sementara (temp/processed/).
FR-3: Word (.docx) Rendering Engine
FR-3.1 Template Binding: Modul harus membaca template bawaan (templates/template_tugas.docx).
FR-3.2 Placeholder Replacement: Mengganti placeholder teks dalam dokumen Word:
{{NAMA}} -> Nama Pengguna
{{NIM}} -> NIM Pengguna
{{MATA_KULIAH}} -> Nama Mata Kuliah
{{JUDUL_TUGAS}} -> Judul/Nomor Tugas
{{TANGGAL}} -> Tanggal (format: DD MMMM YYYY)
FR-3.3 Image Placement:
Foto-foto yang telah diproses dimasukkan secara berurutan setelah tabel cover / header.
Setiap foto ditempatkan pada halaman baru (Page Break) atau ditata rapi secara berurutan.
Ukuran foto diatur secara otomatis agar pas dengan lebar margin dokumen (misalnya: Width = 16 cm, dengan mempertahankan Aspect Ratio).
FR-4: PDF Conversion Engine
FR-4.1 Conversion: Mengonversi file .docx hasil render menjadi .pdf.
FR-4.2 Windows Native Support: Menggunakan pustaka docx2pdf yang memanfaatkan MS Word COM Interface jika berjalan di Windows.
FR-4.3 Fallback Engine: Jika MS Word tidak terdeteksi atau berjalan di OS bukan Windows, sistem harus mendukung panggilan perintah CLI LibreOffice (soffice --headless --convert-to pdf).
FR-5: File Naming & Output Management
FR-5.1 Naming Standard: Nama file output harus mengikuti format yang dikonfigurasi:
[NIM]_[Nama]_[MataKuliah]_[JudulTugas].pdf (semua spasi diubah menjadi _ atau disesuaikan).
FR-5.2 Cleanup Routine: Setelah file PDF berhasil dikirim ke pengguna, seluruh gambar mentah, gambar olahan, dan file temporary di folder temp/ harus dihapus secara otomatis.
6. Non-Functional Requirements
NFR-1 Robustness: Bot harus menangani kasus saat pengguna mengirim gambar berkuran besar (hingga 20 MB) tanpa mengalami timeout atau crash.
NFR-2 Processing Speed: Waktu pemrosesan dari perintah /selesai hingga file PDF terkirim tidak boleh melebihi 15 detik untuk 5 lembar foto di spesifikasi PC rata-rata (i5/Ryzen 5, 8GB RAM).
NFR-3 Code Maintainability: Kode program harus modular, menggunakan prinsip Clean Code, terbagi atas modul UI (Bot), Modul Image, Modul Docx, dan Modul Utils.
NFR-4 Privacy & Security: Bot berjalan secara lokal (127.0.0.1), token bot disimpan dalam file .env yang terisolasi dan tidak di-commit ke repositori public.
7. Directory & File Structure
Berikut adalah struktur folder wajib yang harus dibuat oleh AI Agent:
auto-assignment-bot/
├── config/
│   └── profile.json             # Menyimpan data diri default user
├── templates/
│   └── template_tugas.docx      # Template dasar Microsoft Word
├── temp/                        # Folder sementara untuk pemrosesan file
│   ├── raw/
│   └── processed/
├── output/                      # Folder penyimpanan lokal hasil PDF
├── src/
│   ├── __init__.py
│   ├── config_manager.py        # Pengelola profil & config
│   ├── image_processor.py       # Engine OpenCV (crop, filter, scan effect)
│   ├── doc_generator.py         # Engine python-docx
│   ├── pdf_converter.py         # Engine konversi docx ke pdf
│   └── bot_handlers.py          # Handler command Telegram
├── .env.example                 # Contoh file environment (TELEGRAM_BOT_TOKEN)
├── .gitignore
├── main.py                      # Entry point aplikasi
├── requirements.txt             # Daftar dependensi Python
└── README.md                    # Dokumentasi cara penggunaan


8. Detailed Step-by-Step Implementation Guide for AI Agent
AI Agent diminta mengeksekusi proyek ini dalam 5 Tahap Utama:
Phase 1: Environment & Project Setup
Buat struktur folder sesuai seksi 7.
Buat requirements.txt berisi:
python-telegram-bot>=20.0
opencv-python>=4.8.0
Pillow>=10.0.0
numpy>=1.24.0
python-docx>=0.8.11
docx2pdf>=0.1.8
python-dotenv>=1.0.0


Buat file .env.example dan .env yang memuat TELEGRAM_BOT_TOKEN=.
Buat file templates/template_tugas.docx sederhana yang berisi Header Data Diri (Placeholder: {{NAMA}}, {{NIM}}, {{MATA_KULIAH}}, {{JUDUL_TUGAS}}, {{TANGGAL}}) menggunakan python-docx jika template belum ada.
Phase 2: Core Image Processor (src/image_processor.py)
Implementasikan fungsi-fungsi berikut menggunakan OpenCV:
fix_orientation(image_path) -> Image: Membaca metadata EXIF dan memutar foto jika terbalik.
enhance_scanner_effect(image) -> Image:
Convert ke Grayscale.
Gunakan cv2.adaptiveThreshold atau kombinasi cv2.addWeighted untuk mempertajam kontras latar putih dan tulisan hitam.
auto_crop_paper(image) -> Image:
cv2.Canny untuk mendeteksi tepi.
Find contours, cari kontur 4-titik terbesar.
Lakukan cv2.getPerspectiveTransform dan cv2.warpPerspective. Jika gagal, fallback ke image.
process_image_pipeline(input_path, output_path) -> str: Menggabungkan semua fungsi di atas dan menyimpan hasilnya.
Phase 3: Document & PDF Engine (src/doc_generator.py & src/pdf_converter.py)
generate_docx(data_dict, image_paths, output_docx_path):
Buka templates/template_tugas.docx.
Iterasi semua paragraf dan tabel, ganti string placeholder dengan isi data_dict.
Tambahkan foto dari image_paths ke dalam dokumen dengan mengatur lebar relatif (Inches atau Cm).
Simpan ke output_docx_path.
convert_to_pdf(docx_path, pdf_path):
Eksekusi docx2pdf.convert().
Tambahkan try-except block untuk mendeteksi ketersediaan Microsoft Word.
Phase 4: Telegram Bot Integration (src/bot_handlers.py & main.py)
Buat ConversationHandler dengan state:
SET_MATKUL: Menerima input nama mata kuliah.
SET_JUDUL: Menerima input judul tugas.
UPLOAD_IMAGES: Menerima kiriman foto berulang kali dan menyimpannya ke temp/raw/.
Tambahkan command /selesai untuk men-trigger antrean pemrosesan:
Memanggil image_processor.
Memanggil doc_generator.
Memanggil pdf_converter.
Mengirimkan PDF hasil akhir via context.bot.send_document().
Membersihkan folder temp/.
Phase 5: Verification & Testing
Jalankan unit test sederhana untuk memastikan OpenCV memproses sampel foto dengan baik.
Uji alur pembuatan dokumen Word tanpa bot.
Jalankan python main.py dan lakukan pengujian interaksi dari aplikasi Telegram.
9. Edge Cases & Error Handling Specifications
Kasus 1: Pengguna Mengirim Gambar sebagai "Document" (Uncompressed)
Handling: Bot harus mengenali pesan tipe Message.document selain Message.photo agar kualitas asli foto tetap terjaga jika pengguna memilih kirim sebagai berkas.
Kasus 2: MS Word Tidak Terinstall di Laptop Pengguna
Handling: pdf_converter.py harus menangkap exception dan memberikan peringatan yang jelas di konsol/Telegram bahwa Microsoft Word atau LibreOffice diperlukan untuk fungsi konversi PDF.
Kasus 3: Foto Miring 90 atau 180 Derajat
Handling: Berikan opsi command cepat /rotate atau otomatiskan rotasi berdasarkan rasio aspek (Kertas A4 umumnya Portrait).
Kasus 4: Nama File Memiliki Karakter Ilegal (misal: / \ : * ? " < > |)
Handling: Terapkan sanitasi string pada nama file output menggunakan ekspresi reguler (Regex) untuk menghilangkan karakter terlarang OS.
10. Acceptance Criteria (Definisi Selesai)
[ ] Bot Telegram dapat dinyalakan secara lokal tanpa error.
[ ] Pengguna dapat menyimpan data diri (Nama & NIM) satu kali via /setup.
[ ] Bot dapat menerima minimal 1-10 foto sekaligus dalam satu sesi tugas.
[ ] Foto yang diproses memiliki latar putih bersih dan tulisan tulisan tangan yang terbaca jelas.
[ ] Dokumen .docx yang dihasilkan terisi otomatis data dirinya dan foto tersusun rapi.
[ ] File .pdf tergenerasi secara otomatis dan terkirim ke Telegram pengguna.
[ ] Folder temporary bersih setelah proses selesai.
