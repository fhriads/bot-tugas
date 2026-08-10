import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from src.config_manager import load_profile, save_profile
from src.image_processor import process_image_pipeline
from src.doc_generator import generate_docx
from src.pdf_converter import convert_to_pdf, convert_scanned_pdf_to_docx

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"

# Conversation States for /setup
SETUP_NAMA, SETUP_NIM = range(2)

# Conversation States for /tugas & /convert
WAITING_MATKUL, WAITING_JUDUL, WAITING_IMAGES, SELECT_FILTER, SELECT_FORMAT, WAITING_PDF_FILE = range(2, 8)


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes string to make it safe for OS file paths by removing illegal characters.
    """
    sanitized = re.sub(r'[\/:*?"<>|]', '_', filename)
    sanitized = re.sub(r'\s+', '_', sanitized)
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_')


def cleanup_user_temp(user_id: int):
    """
    Cleans up user specific temporary raw and processed folders.
    """
    raw_dir = TEMP_DIR / "raw" / str(user_id)
    proc_dir = TEMP_DIR / "processed" / str(user_id)
    if raw_dir.exists():
        shutil.rmtree(raw_dir, ignore_errors=True)
    if proc_dir.exists():
        shutil.rmtree(proc_dir, ignore_errors=True)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command displaying main interactive menu with 2 buttons."""
    profile = load_profile()
    welcome_text = (
        "🤖 *Selamat datang di Telegram Assignment & Converter Bot!*\n\n"
        "Silakan pilih layanan yang ingin Anda gunakan:\n\n"
        "1. 📚 *Buat Tugas Baru:* Konversi foto tugas tulisan tangan ke template Word (.docx) & PDF.\n"
        "2. 🔄 *Convert PDF ke Word:* Ubah file PDF (hasil CamScanner/foto) ke file Word (.docx) tanpa ada gambar hilang.\n\n"
        f"📋 *Profil saat ini:* `{profile['nama']}` (`{profile['nim']}`)\n"
        "Gunakan /setup jika ingin mengubah Nama & NIM."
    )
    keyboard = [
        [
            InlineKeyboardButton("📚 Buat Tugas Baru", callback_data="menu_start_tugas")
        ],
        [
            InlineKeyboardButton("🔄 Convert PDF ke Word (.docx)", callback_data="menu_start_convert")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /profile command."""
    profile = load_profile()
    text = (
        "👤 *Profil Pengguna Tersimpan:*\n\n"
        f"• *Nama:* {profile['nama']}\n"
        f"• *NIM:* {profile['nim']}\n\n"
        "Gunakan perintah /setup untuk memperbarui profil ini."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# --- Profile Setup Workflow ---

async def setup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the /setup conversation flow."""
    await update.message.reply_text(
        "✏️ *Pengaturan Profil Pengguna*\n\n"
        "Silakan masukkan *Nama Lengkap* Anda:",
        parse_mode="Markdown"
    )
    return SETUP_NAMA


async def setup_nama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives Nama and asks for NIM."""
    context.user_data["setup_nama"] = update.message.text.strip()
    await update.message.reply_text(
        "Silakan masukkan *NIM (Nomor Induk Mahasiswa)* Anda:",
        parse_mode="Markdown"
    )
    return SETUP_NIM


async def setup_nim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives NIM and saves profile."""
    nim = update.message.text.strip()
    nama = context.user_data.get("setup_nama", "")

    saved = save_profile(nama, nim)

    await update.message.reply_text(
        "✅ *Profil berhasil disimpan!*\n\n"
        f"• *Nama:* {saved['nama']}\n"
        f"• *NIM:* {saved['nim']}\n\n"
        "Ketik /tugas untuk mulai membuat dokumen tugas.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# --- Assignment Task Submission Workflow ---

async def tugas_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the /tugas submission conversation flow."""
    user_id = update.effective_user.id
    cleanup_user_temp(user_id)

    context.user_data["images"] = []
    context.user_data["judul_tugas"] = ""

    msg_text = (
        "📚 *Inisialisasi Tugas Baru*\n\n"
        "Silakan masukkan *Nama Mata Kuliah* (contoh: `Kalkulus II`):"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(msg_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg_text, parse_mode="Markdown")

    return WAITING_MATKUL


async def tugas_matkul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives Mata Kuliah and asks for Judul Tugas."""
    context.user_data["matkul"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 *Nama / Judul Tugas (Opsional)*\n\n"
        "Silakan masukkan Judul/Nomor Tugas (contoh: `Tugas 1` atau `Tugas 2 - Turunan`).\n\n"
        "💡 *Tips:* Ketik /skip jika tidak ingin menambahkan nama tugas pada nama file.",
        parse_mode="Markdown"
    )
    return WAITING_JUDUL


async def tugas_judul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives Judul Tugas and asks for images."""
    context.user_data["judul_tugas"] = update.message.text.strip()
    await update.message.reply_text(
        "📷 *Kirim Foto Lembar Jawaban*\n\n"
        "Silakan kirimkan foto-foto lembar jawaban Anda secara berurutan.\n"
        "• Anda dapat memilih foto sebagai *Photo* maupun *Document* (uncompressed).\n"
        "• Jika semua foto sudah selesai dikirim, ketik /selesai",
        parse_mode="Markdown"
    )
    return WAITING_IMAGES


async def skip_judul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skips entering Judul Tugas and proceeds directly to image upload."""
    context.user_data["judul_tugas"] = ""
    await update.message.reply_text(
        "📷 *Kirim Foto Lembar Jawaban*\n\n"
        "Silakan kirimkan foto-foto lembar jawaban Anda secara berurutan.\n"
        "• Anda dapat memilih foto sebagai *Photo* maupun *Document* (uncompressed).\n"
        "• Jika semua foto sudah selesai dikirim, ketik /selesai",
        parse_mode="Markdown"
    )
    return WAITING_IMAGES


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives an uploaded photo or document image and saves to temp/raw/{user_id}/."""
    user_id = update.effective_user.id
    raw_dir = TEMP_DIR / "raw" / str(user_id)
    raw_dir.mkdir(parents=True, exist_ok=True)

    img_file = None
    file_ext = ".jpg"

    if update.message.photo:
        photo = update.message.photo[-1]
        img_file = await photo.get_file()
    elif update.message.document:
        doc = update.message.document
        mime = doc.mime_type or ""
        if not (mime.startswith("image/") or doc.file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))):
            await update.message.reply_text("⚠️ Berkas yang Anda kirim bukan format gambar! Harap kirim file foto (JPG/PNG).")
            return WAITING_IMAGES
        img_file = await doc.get_file()
        ext = Path(doc.file_name).suffix
        if ext:
            file_ext = ext.lower()

    if img_file:
        images_list = context.user_data.get("images", [])
        idx = len(images_list) + 1
        save_path = raw_dir / f"page_{idx:03d}{file_ext}"

        await img_file.download_to_drive(save_path)
        images_list.append(str(save_path))
        context.user_data["images"] = images_list

        await update.message.reply_text(
            f"📄 Foto ke-{idx} telah diterima.\n"
            "Kirim foto berikutnya atau ketik /selesai jika sudah lengkap."
        )

    return WAITING_IMAGES


async def selesai_tugas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks the user to choose filter mode (Normal vs Scanner BETA)."""
    images = context.user_data.get("images", [])

    if not images:
        await update.message.reply_text("⚠️ Anda belum mengirimkan foto lembar jawaban sama sekali! Harap kirim minimal 1 foto.")
        return WAITING_IMAGES

    keyboard = [
        [
            InlineKeyboardButton("📷 Foto Asli / Normal (Rekomendasi)", callback_data="mode_original")
        ],
        [
            InlineKeyboardButton("⚡ Efek Scanner (BETA)", callback_data="mode_scanner")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎨 *Pilih Mode Tampilan Gambar:*\n\n"
        "1. 📷 *Foto Asli / Normal:* Menggunakan foto asli Anda tanpa mengubah warna/kontras (Direkomendasikan).\n"
        "2. ⚡ *Efek Scanner (BETA):* Mengubah latar belakang menjadi putih seperti scanner (Fitur eksperimental).",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECT_FILTER


async def choose_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves filter mode choice and asks for output document format."""
    query = update.callback_query
    await query.answer()

    use_scanner = (query.data == "mode_scanner")
    context.user_data["use_scanner_effect"] = use_scanner

    filter_name = "⚡ Efek Scanner (BETA)" if use_scanner else "📷 Foto Asli (Normal)"

    keyboard = [
        [
            InlineKeyboardButton("📄 File PDF", callback_data="fmt_pdf"),
            InlineKeyboardButton("📝 File Word (DOCX)", callback_data="fmt_docx"),
        ],
        [
            InlineKeyboardButton("📦 Keduanya (DOCX & PDF)", callback_data="fmt_both")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Selected Mode: *{filter_name}*\n\n"
        "📄 *Pilih Format File Output:*\n"
        "Silakan pilih format file dokumen yang ingin dikirimkan bot:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECT_FORMAT


async def process_and_send_documents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes images and generates/sends the selected document format(s)."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    selected_fmt = query.data  # 'fmt_pdf', 'fmt_docx', 'fmt_both'
    images = context.user_data.get("images", [])
    use_scanner_effect = context.user_data.get("use_scanner_effect", False)

    profile = load_profile()
    matkul = context.user_data.get("matkul", "Mata Kuliah")
    judul_tugas = context.user_data.get("judul_tugas", "").strip()
    tanggal_str = datetime.now().strftime("%d %B %Y")

    await query.edit_message_text(
        "🔄 *Processing... (Step 1/3: Processing & Scaling Images)*",
        parse_mode="Markdown"
    )

    try:
        # Step 1: Process Images
        proc_dir = TEMP_DIR / "processed" / str(user_id)
        proc_dir.mkdir(parents=True, exist_ok=True)

        processed_images = []
        for idx, raw_p in enumerate(images):
            out_p = proc_dir / f"proc_{idx:03d}.jpg"
            process_image_pipeline(raw_p, out_p, use_scanner_effect=use_scanner_effect)
            processed_images.append(out_p)

        # Step 2: Generate Word Document
        await query.edit_message_text(
            "🔄 *Processing... (Step 2/3: Generating Word Document)*",
            parse_mode="Markdown"
        )

        clean_nim = sanitize_filename(profile["nim"])
        clean_nama = sanitize_filename(profile["nama"])
        clean_matkul = sanitize_filename(matkul)
        clean_tugas = sanitize_filename(judul_tugas) if judul_tugas else ""

        if clean_tugas:
            filename_stem = f"{clean_nim}_{clean_nama}_{clean_matkul}_{clean_tugas}"
        else:
            filename_stem = f"{clean_nim}_{clean_nama}_{clean_matkul}"

        output_docx_path = OUTPUT_DIR / f"{filename_stem}.docx"
        output_pdf_path = OUTPUT_DIR / f"{filename_stem}.pdf"

        # Save last generated file paths in user_data for quick fetching
        context.user_data["last_docx_path"] = str(output_docx_path)
        context.user_data["last_pdf_path"] = str(output_pdf_path)
        context.user_data["last_filename_stem"] = filename_stem

        display_matkul = f"{matkul} ({judul_tugas})" if judul_tugas else matkul

        data_dict = {
            "nama": profile["nama"],
            "nim": profile["nim"],
            "mata_kuliah": display_matkul,
            "tanggal": tanggal_str
        }

        generate_docx(data_dict, processed_images, output_docx_path)

        # Step 3: Convert to PDF if required
        need_pdf = selected_fmt in ["fmt_pdf", "fmt_both"]
        need_docx = selected_fmt in ["fmt_docx", "fmt_both"]

        if need_pdf:
            await query.edit_message_text(
                "🔄 *Processing... (Step 3/3: Converting to PDF)*",
                parse_mode="Markdown"
            )
            convert_to_pdf(output_docx_path, output_pdf_path)

        # Step 4: Send Document(s) to User
        await query.edit_message_text(
            "🔄 *Uploading file(s)...*",
            parse_mode="Markdown"
        )

        mode_text = "⚡ Scanner (BETA)" if use_scanner_effect else "📷 Foto Asli (Normal)"
        tugas_text = f"\n• *Tugas:* {judul_tugas}" if judul_tugas else ""

        caption_text = (
            f"✅ *Dokumen Tugas Berhasil Dibuat!*\n\n"
            f"• *Nama:* {profile['nama']}\n"
            f"• *NIM:* {profile['nim']}\n"
            f"• *Matkul:* {matkul}"
            f"{tugas_text}\n"
            f"• *Mode Gambar:* {mode_text}\n"
            f"• *Jumlah Halaman:* {len(processed_images)}"
        )

        # Prepare quick fetch buttons if only one format was sent (fixed 64-byte limit)
        btn_word = [InlineKeyboardButton("📝 Kirimkan File Word (DOCX) Juga", callback_data="get_other_docx")]
        btn_pdf = [InlineKeyboardButton("📄 Kirimkan File PDF Juga", callback_data="get_other_pdf")]

        if selected_fmt == "fmt_docx":
            # Sent Word only -> Offer PDF button
            with open(output_docx_path, "rb") as f_docx:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=f_docx,
                    filename=output_docx_path.name,
                    caption=caption_text,
                    reply_markup=InlineKeyboardMarkup([btn_pdf]),
                    parse_mode="Markdown"
                )
        elif selected_fmt == "fmt_pdf":
            # Sent PDF only -> Offer Word button
            with open(output_pdf_path, "rb") as f_pdf:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=f_pdf,
                    filename=output_pdf_path.name,
                    caption=caption_text,
                    reply_markup=InlineKeyboardMarkup([btn_word]),
                    parse_mode="Markdown"
                )
        else:
            # Sent Both
            with open(output_docx_path, "rb") as f_docx:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=f_docx,
                    filename=output_docx_path.name,
                    parse_mode="Markdown"
                )
            with open(output_pdf_path, "rb") as f_pdf:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=f_pdf,
                    filename=output_pdf_path.name,
                    caption=caption_text,
                    parse_mode="Markdown"
                )

        await query.delete_message()

    except Exception as e:
        print(f"[BotHandler] Error during task processing: {e}")
        await query.edit_message_text(
            f"❌ *Terjadi Kesalahan saat Pemrosesan:*\n`{str(e)}`",
            parse_mode="Markdown"
        )
    finally:
        cleanup_user_temp(user_id)

    return ConversationHandler.END


async def get_other_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback handler for fetching the alternative format (DOCX or PDF) after task completion.
    """
    query = update.callback_query
    await query.answer()

    data = query.data  # e.g. "get_other_docx" or "get_other_pdf" or legacy "get_other_docx:stem"
    user_id = query.from_user.id

    parts = data.split(":", 1)
    action = parts[0]
    filename_stem = parts[1] if len(parts) > 1 else context.user_data.get("last_filename_stem", "")

    if action == "get_other_docx":
        docx_path = None
        if filename_stem:
            docx_path = OUTPUT_DIR / f"{filename_stem}.docx"
        elif context.user_data.get("last_docx_path"):
            docx_path = Path(context.user_data["last_docx_path"])

        if docx_path and docx_path.exists():
            with open(docx_path, "rb") as f_docx:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=f_docx,
                    filename=docx_path.name,
                    caption="📝 *Ini file Word (.docx) Anda.*",
                    parse_mode="Markdown"
                )
        else:
            await query.message.reply_text("⚠️ Berkas Word tidak ditemukan di penyimpanan lokal.")

    elif action == "get_other_pdf":
        pdf_path = None
        docx_path = None

        if filename_stem:
            pdf_path = OUTPUT_DIR / f"{filename_stem}.pdf"
            docx_path = OUTPUT_DIR / f"{filename_stem}.docx"
        else:
            if context.user_data.get("last_pdf_path"):
                pdf_path = Path(context.user_data["last_pdf_path"])
            if context.user_data.get("last_docx_path"):
                docx_path = Path(context.user_data["last_docx_path"])

        if pdf_path and not pdf_path.exists() and docx_path and docx_path.exists():
            status_msg = await query.message.reply_text("🔄 *Mengonversi ke PDF...*", parse_mode="Markdown")
            try:
                convert_to_pdf(docx_path, pdf_path)
                await status_msg.delete()
            except Exception as e:
                await status_msg.edit_text(f"❌ Gagal mengonversi PDF: `{e}`", parse_mode="Markdown")
                return

        if pdf_path and pdf_path.exists():
            with open(pdf_path, "rb") as f_pdf:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=f_pdf,
                    filename=pdf_path.name,
                    caption="📄 *Ini file PDF Anda.*",
                    parse_mode="Markdown"
                )
        else:
            await query.message.reply_text("⚠️ Berkas PDF tidak ditemukan.")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels current active conversation and cleans up temp files."""
    user_id = update.effective_user.id
    cleanup_user_temp(user_id)

    await update.message.reply_text(
        "❌ Sesi dibatalkan. Folder sementara telah dibersihkan.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# --- PDF to Word Conversion Workflow ---

async def convert_pdf_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the /convert PDF to DOCX flow."""
    user_id = update.effective_user.id
    cleanup_user_temp(user_id)

    msg_text = (
        "🔄 *Konversi PDF ke Word (.docx)*\n\n"
        "Silakan kirimkan berkas *PDF* (misal hasil scan CamScanner / dokumen tugas) yang ingin dikonversi ke Word.\n\n"
        "💡 Ketik /cancel jika ingin membatalkan."
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(msg_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg_text, parse_mode="Markdown")

    return WAITING_PDF_FILE


async def receive_pdf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives uploaded PDF document and converts it to DOCX using PyMuPDF."""
    user_id = update.effective_user.id
    doc = update.message.document

    if not doc or not (doc.mime_type == "application/pdf" or doc.file_name.lower().endswith(".pdf")):
        await update.message.reply_text(
            "⚠️ Berkas yang Anda kirimkan bukan format PDF!\n"
            "Harap kirimkan dokumen dengan format `.pdf`."
        )
        return WAITING_PDF_FILE

    raw_dir = TEMP_DIR / "raw" / str(user_id)
    raw_dir.mkdir(parents=True, exist_ok=True)

    input_pdf_path = raw_dir / doc.file_name
    pdf_stem = Path(doc.file_name).stem
    output_docx_path = OUTPUT_DIR / f"{pdf_stem}_converted.docx"

    status_msg = await update.message.reply_text("🔄 *Mengunduh dan mengonversi PDF ke Word (.docx)...*", parse_mode="Markdown")

    try:
        # Download PDF file
        pdf_file = await doc.get_file()
        await pdf_file.download_to_drive(input_pdf_path)

        # Convert PDF to DOCX using PyMuPDF (fitz)
        convert_scanned_pdf_to_docx(input_pdf_path, output_docx_path)

        # Send converted DOCX back to user
        await status_msg.edit_text("🔄 *Mengirimkan file Word (.docx)...*", parse_mode="Markdown")

        with open(output_docx_path, "rb") as f_docx:
            await context.bot.send_document(
                chat_id=user_id,
                document=f_docx,
                filename=output_docx_path.name,
                caption=(
                    "✅ *Konversi PDF ke Word Berhasil!*\n\n"
                    "• Semua gambar & halaman dari PDF telah dimasukkan ke file Word tanpa ada yang hilang atau bertumpuk."
                ),
                parse_mode="Markdown"
            )
        await status_msg.delete()

    except Exception as e:
        print(f"[BotHandler] Error converting PDF to DOCX: {e}")
        await status_msg.edit_text(
            f"❌ *Terjadi Kesalahan saat Konversi PDF:*\n`{str(e)}`",
            parse_mode="Markdown"
        )
    finally:
        cleanup_user_temp(user_id)

    return ConversationHandler.END

