import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
PROFILE_PATH = CONFIG_DIR / "profile.json"


def get_telegram_token() -> str:
    """Retrieves Telegram Bot Token from environment variables."""
    return os.getenv("TELEGRAM_BOT_TOKEN", "").strip()


def load_profile() -> dict:
    """
    Loads profile data (nama, nim) from config/profile.json.
    Falls back to environment variables or defaults if file missing or invalid.
    """
    default_profile = {
        "nama": os.getenv("DEFAULT_NAMA", "Mahasiswa"),
        "nim": os.getenv("DEFAULT_NIM", "1234567890"),
    }

    if not PROFILE_PATH.exists():
        save_profile(default_profile["nama"], default_profile["nim"])
        return default_profile

    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "nama": data.get("nama", default_profile["nama"]),
                "nim": data.get("nim", default_profile["nim"]),
            }
    except Exception as e:
        print(f"[ConfigManager] Error reading profile.json ({e}), using default profile.")
        return default_profile


def save_profile(nama: str, nim: str) -> dict:
    """
    Saves user profile data (nama, nim) into config/profile.json.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    profile_data = {
        "nama": nama.strip(),
        "nim": nim.strip(),
    }
    try:
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ConfigManager] Error saving profile.json: {e}")

    return profile_data
