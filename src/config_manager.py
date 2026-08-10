import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
OLD_PROFILE_PATH = CONFIG_DIR / "profile.json"
PROFILES_PATH = CONFIG_DIR / "profiles.json"


def get_telegram_token() -> str:
    """Retrieves Telegram Bot Token from environment variables."""
    return os.getenv("TELEGRAM_BOT_TOKEN", "").strip()


def load_profile(user_id: int | str = None) -> dict:
    """
    Loads profile data (nama, nim) for a specific user_id from config/profiles.json.
    Falls back to environment variables or defaults if user profile missing.
    """
    default_profile = {
        "nama": os.getenv("DEFAULT_NAMA", "Mahasiswa"),
        "nim": os.getenv("DEFAULT_NIM", "1234567890"),
    }

    if user_id is None:
        return default_profile

    user_key = str(user_id)

    # Backward compatibility: Migrate old single profile.json if profiles.json doesn't exist
    if not PROFILES_PATH.exists() and OLD_PROFILE_PATH.exists():
        try:
            with open(OLD_PROFILE_PATH, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                if old_data.get("nama") and old_data.get("nim"):
                    save_profile(user_key, old_data["nama"], old_data["nim"])
                    return old_data
        except Exception:
            pass

    if not PROFILES_PATH.exists():
        return default_profile

    try:
        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)
            if user_key in profiles:
                user_data = profiles[user_key]
                return {
                    "nama": user_data.get("nama", default_profile["nama"]),
                    "nim": user_data.get("nim", default_profile["nim"]),
                }
    except Exception as e:
        print(f"[ConfigManager] Error reading profiles.json ({e}), using default profile.")

    return default_profile


def save_profile(user_id: int | str, nama: str, nim: str) -> dict:
    """
    Saves user profile data (nama, nim) for a specific Telegram user_id into config/profiles.json.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    user_key = str(user_id)
    profile_data = {
        "nama": nama.strip(),
        "nim": nim.strip(),
    }

    profiles = {}
    if PROFILES_PATH.exists():
        try:
            with open(PROFILES_PATH, "r", encoding="utf-8") as f:
                profiles = json.load(f)
        except Exception:
            profiles = {}

    profiles[user_key] = profile_data

    try:
        with open(PROFILES_PATH, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ConfigManager] Error saving profiles.json: {e}")

    return profile_data

