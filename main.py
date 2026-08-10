import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.request import HTTPXRequest

from src.config_manager import get_telegram_token, load_profile
from create_template import generate_default_template, TEMPLATES_DIR, ASSETS_DIR
from src.bot_handlers import (
    start_command,
    profile_command,
    cancel_command,
    setup_start,
    setup_nama,
    setup_nim,
    tugas_start,
    tugas_matkul,
    tugas_judul,
    skip_judul,
    receive_image,
    selesai_tugas,
    choose_filter,
    process_and_send_documents,
    get_other_file,
    convert_pdf_start,
    receive_pdf_file,
    SETUP_NAMA,
    SETUP_NIM,
    WAITING_MATKUL,
    WAITING_JUDUL,
    WAITING_IMAGES,
    SELECT_FILTER,
    SELECT_FORMAT,
    WAITING_PDF_FILE,
)

BASE_DIR = Path(__file__).resolve().parent


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP server handler for Render Free Web Service health checks."""
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Telegram Bot is running!")

    def log_message(self, format, *args):
        # Suppress verbose HTTP server logs in console
        pass


def start_health_check_server():
    """Starts background HTTP server listening on PORT for Render Web Service."""
    port = int(os.getenv("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        print(f"[HealthCheck] Dummy HTTP server listening on port {port} for Render Free Web Service...")
        server.serve_forever()
    except Exception:
        # Ignore port binding errors silently when running on PythonAnywhere or local dev
        pass


def initialize_environment():
    """Ensures all required project directories and templates exist."""
    directories = [
        BASE_DIR / "config",
        BASE_DIR / "templates",
        BASE_DIR / "assets",
        BASE_DIR / "temp" / "raw",
        BASE_DIR / "temp" / "processed",
        BASE_DIR / "output",
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)

    load_profile()

    tmpl_path = TEMPLATES_DIR / "template_tugas.docx"
    asset_path = ASSETS_DIR / "template.docx"
    if not tmpl_path.exists() or not asset_path.exists():
        print("[Main] Initializing default Word templates...")
        generate_default_template([tmpl_path, asset_path])


def main():
    """Main application entry point."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 60)
    print(" [BOT] Starting Telegram Assignment Converter Bot ")
    print("=" * 60)

    # Start dummy HTTP health check server in background thread for Render Free Web Service
    threading.Thread(target=start_health_check_server, daemon=True).start()

    initialize_environment()

    token = get_telegram_token()
    if not token or token == "your_telegram_bot_token_here":
        print("\n❌ TELEGRAM_BOT_TOKEN belum dikonfigurasi!")
        print("Buka file '.env' di direktori proyek ini dan isi token bot Telegram Anda dari @BotFather.")
        print("Contoh: TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ\n")
        sys.exit(1)

    # Configure proxy for PythonAnywhere or environments requiring HTTP proxy
    proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("https_proxy") or os.getenv("http_proxy")
    if not proxy_url and ("PYTHONANYWHERE_DOMAIN" in os.environ or "PYTHONANYWHERE_SITE" in os.environ):
        proxy_url = "http://proxy.server:3128"

    if proxy_url:
        print(f"[Main] Configuring HTTP Proxy: {proxy_url}")
        req = HTTPXRequest(
            proxy=proxy_url,
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
            media_write_timeout=60.0,
        )
        app = ApplicationBuilder().token(token).request(req).build()
    else:
        req = HTTPXRequest(
            connect_timeout=20.0,
            read_timeout=20.0,
            write_timeout=20.0,
            media_write_timeout=60.0,
        )
        app = ApplicationBuilder().token(token).request(req).build()

    # 1. Setup / Profile Conversation Handler
    setup_conv = ConversationHandler(
        entry_points=[
            CommandHandler("setup", setup_start),
            CommandHandler("setprofile", setup_start),
        ],
        states={
            SETUP_NAMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_nama)],
            SETUP_NIM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_nim)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )

    # 2. Assignment Submission Conversation Handler
    tugas_conv = ConversationHandler(
        entry_points=[
            CommandHandler("tugas", tugas_start),
            CommandHandler("buat_tugas", tugas_start),
            CallbackQueryHandler(tugas_start, pattern="^menu_start_tugas$"),
        ],
        states={
            WAITING_MATKUL: [MessageHandler(filters.TEXT & ~filters.COMMAND, tugas_matkul)],
            WAITING_JUDUL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tugas_judul),
                CommandHandler("skip", skip_judul),
            ],
            WAITING_IMAGES: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, receive_image),
                CommandHandler("selesai", selesai_tugas),
            ],
            SELECT_FILTER: [
                CallbackQueryHandler(choose_filter, pattern="^mode_")
            ],
            SELECT_FORMAT: [
                CallbackQueryHandler(process_and_send_documents, pattern="^fmt_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        per_chat=True,
        per_user=True,
        per_message=False,
    )

    # 3. PDF to Word Conversion Conversation Handler
    convert_conv = ConversationHandler(
        entry_points=[
            CommandHandler("convert", convert_pdf_start),
            CommandHandler("pdf2word", convert_pdf_start),
            CallbackQueryHandler(convert_pdf_start, pattern="^menu_start_convert$"),
        ],
        states={
            WAITING_PDF_FILE: [
                MessageHandler(filters.Document.ALL, receive_pdf_file)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        per_chat=True,
        per_user=True,
        per_message=False,
    )

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(setup_conv)
    app.add_handler(tugas_conv)
    app.add_handler(convert_conv)
    app.add_handler(CallbackQueryHandler(get_other_file, pattern="^get_other_"))
    app.add_handler(CommandHandler("cancel", cancel_command))

    print("[Main] Bot Telegram siap dan mendengarkan pesan (Polling)...")
    app.run_polling()


if __name__ == "__main__":
    main()
