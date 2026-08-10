import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image
import io

GWIS_SYSTEM_INSTRUCTION = (
    "Kamu adalah Gwis, seorang asisten perkuliahan wanita (cewek) yang ramah, santun, cerdas, "
    "dan selalu siap membantu mahasiswa mengelola tugas dan jadwal kuliah. Gunakan bahasa Indonesia "
    "yang santai tapi sopan, dengan gaya sapaan ramah dan perhatian (misal menggunakan kata sapaan 'Gwis' dan emotikon 🌸✨)."
)

# Preferred Gemini models for the new google-genai SDK
GEMINI_MODELS = ["gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-flash-latest"]


def get_gemini_api_key() -> str:
    """Retrieves Gemini API Key from environment variables."""
    return os.getenv("GEMINI_API_KEY", "").strip()


def _get_genai_client():
    """Initializes and returns new official google-genai Client if API Key is configured."""
    api_key = get_gemini_api_key()
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[AIProcessor] Failed to initialize google-genai Client: {e}")
        return None


def parse_deadline_with_ai(user_text: str, current_time: datetime = None) -> dict:
    """
    Parses natural language deadline text into a structured dictionary using Gemini AI.
    Returns: {"matkul": str, "tugas": str, "deadline": "YYYY-MM-DD HH:MM"}
    """
    if current_time is None:
        current_time = datetime.now()

    current_time_str = current_time.strftime("%Y-%m-%d %H:%M (%A)")
    client = _get_genai_client()

    if not client:
        print("[AIProcessor] Notice: GEMINI_API_KEY not configured or client error, using smart fallback parser.")
        return _fallback_parse_deadline(user_text, current_time)

    prompt = (
        f"{GWIS_SYSTEM_INSTRUCTION}\n\n"
        f"Waktu dan tanggal saat ini adalah: {current_time_str}.\n"
        f"Tugas kamu adalah menganalisis pesan pengguna berikut dan menguraikan informasi deadline tugasnya:\n"
        f"Pesan pengguna: \"{user_text}\"\n\n"
        f"Kembalikan HANYA JSON valid tanpa format markdown tambahan dalam struktur berikut:\n"
        f"{{\n"
        f'  "matkul": "Nama Mata Kuliah",\n'
        f'  "tugas": "Nama / Judul Tugas",\n'
        f'  "deadline": "YYYY-MM-DD HH:MM"\n'
        f"}}\n"
        f"Catatan:\n"
        f"- Hitung tanggal 'besok', 'lusa', 'jumat depan', dll berdasarkan waktu saat ini ({current_time_str}).\n"
        f"- Jika jam tidak disebutkan secara spesifik, gunakan default '23:59'.\n"
        f"- Jika nama matkul tidak jelas, gunakan potongan judul tugas utama."
    )

    resp_text = None
    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                resp_text = response.text.strip()
                break
        except Exception as e:
            print(f"[AIProcessor] Model '{model_name}' failed ({e}). Trying next model...")

    if not resp_text:
        return _fallback_parse_deadline(user_text, current_time)

    try:
        resp_text = re.sub(r"^```json\s*", "", resp_text)
        resp_text = re.sub(r"^```\s*", "", resp_text)
        resp_text = re.sub(r"\s*```$", "", resp_text)

        data = json.loads(resp_text)
        return {
            "matkul": data.get("matkul", "Mata Kuliah").strip(),
            "tugas": data.get("tugas", user_text).strip(),
            "deadline": data.get("deadline", (current_time + timedelta(days=1)).strftime("%Y-%m-%d 23:59")).strip(),
        }
    except Exception as e:
        print(f"[AIProcessor] Failed to parse JSON response ({e}). Using fallback parser.")
        return _fallback_parse_deadline(user_text, current_time)


def parse_schedule_from_image_or_text(image_bytes_or_path=None, text_content: str = None) -> dict:
    """
    Parses a class schedule screenshot/photo or raw text using Gemini Vision AI.
    Returns structured dictionary:
    {
      "Senin": [{"matkul": "...", "jam": "08:00 - 10:00", "ruang": "Lab 1", "dosen": "..."}, ...],
      "Selasa": [...]
    }
    """
    client = _get_genai_client()
    if not client:
        print("[AIProcessor] Notice: GEMINI_API_KEY not configured for Schedule OCR.")
        return {}

    try:
        from google.genai import types
    except ImportError:
        print("[AIProcessor] google-genai library missing types.")
        return {}

    prompt = (
        f"{GWIS_SYSTEM_INSTRUCTION}\n\n"
        "Ekstrak jadwal kuliah dari gambar/teks ini menjadi struktur JSON harian.\n"
        "Kembalikan HANYA JSON valid dalam format:\n"
        "{\n"
        '  "Senin": [{"matkul": "...", "jam": "08:00 - 10:00", "ruang": "...", "dosen": "..."}],\n'
        '  "Selasa": [],\n'
        '  "Rabu": [],\n'
        '  "Kamis": [],\n'
        '  "Jumat": [],\n'
        '  "Sabtu": [],\n'
        '  "Minggu": []\n'
        "}\n"
        "Catatan:\n"
        "- Kelompokkan berdasarkan hari (Senin, Selasa, Rabu, Kamis, Jumat, Sabtu, Minggu).\n"
        "- Isi ruang dan dosen jika ada di jadwal, jika tidak ada gunakan string kosong."
    )

    contents = []
    if image_bytes_or_path:
        img_bytes = None
        if isinstance(image_bytes_or_path, (str, Path)):
            with open(image_bytes_or_path, "rb") as f:
                img_bytes = f.read()
        elif isinstance(image_bytes_or_path, bytes):
            img_bytes = image_bytes_or_path
        elif hasattr(image_bytes_or_path, "read"):
            img_bytes = image_bytes_or_path.read()

        if img_bytes:
            contents = [
                prompt,
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
            ]
    else:
        contents = [f"{prompt}\nTeks Jadwal: {text_content}"]

    if not contents:
        return {}

    resp_text = None
    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
            )
            if response and response.text:
                resp_text = response.text.strip()
                break
        except Exception as e:
            print(f"[AIProcessor] Model '{model_name}' vision OCR failed ({e}). Trying next model...")

    if not resp_text:
        return {}

    try:
        resp_text = re.sub(r"^```json\s*", "", resp_text)
        resp_text = re.sub(r"^```\s*", "", resp_text)
        resp_text = re.sub(r"\s*```$", "", resp_text)

        parsed_schedule = json.loads(resp_text)
        return parsed_schedule
    except Exception as e:
        print(f"[AIProcessor] Error parsing schedule JSON ({e}).")
        return {}


def _fallback_parse_deadline(user_text: str, current_time: datetime) -> dict:
    """Smart regex fallback for parsing deadlines when Gemini API is unavailable."""
    text_lower = user_text.lower()
    target_date = current_time

    if "besok" in text_lower:
        target_date = current_time + timedelta(days=1)
    elif "lusa" in text_lower:
        target_date = current_time + timedelta(days=2)

    # Time extraction (e.g. 23:59, jam 11 malam -> 23:00)
    hour = 23
    minute = 59
    time_match = re.search(r'(\d{1,2})[:. ](\d{2})', user_text)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
    elif "malam" in text_lower:
        m_hour = re.search(r'jam\s*(\d{1,2})', text_lower)
        if m_hour:
            h = int(m_hour.group(1))
            hour = h + 12 if h < 12 else h
            minute = 0

    deadline_str = f"{target_date.strftime('%Y-%m-%d')} {hour:02d}:{minute:02d}"

    # Extract matkul clean name
    clean_matkul = user_text
    for kw in ["tugas", "kumpul", "besok", "lusa", "jam", "deadline", "remind"]:
        clean_matkul = re.sub(rf'\b{kw}\b', '', clean_matkul, flags=re.IGNORECASE)
    clean_matkul = re.sub(r'\s+', ' ', clean_matkul).strip()

    return {
        "matkul": clean_matkul if clean_matkul else "Tugas Kuliah",
        "tugas": user_text,
        "deadline": deadline_str
    }
