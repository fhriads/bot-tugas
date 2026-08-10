import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
SCHEDULES_PATH = CONFIG_DIR / "schedules.json"

DAYS_INDONESIA = {
    "Monday": "Senin",
    "Tuesday": "Selasa",
    "Wednesday": "Rabu",
    "Thursday": "Kamis",
    "Friday": "Jumat",
    "Saturday": "Sabtu",
    "Sunday": "Minggu",
}


def _load_all_schedules() -> dict:
    """Reads config/schedules.json."""
    if not SCHEDULES_PATH.exists():
        return {}
    try:
        with open(SCHEDULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ScheduleManager] Error reading schedules.json ({e}).")
        return {}


def _save_all_schedules(data: dict):
    """Writes config/schedules.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SCHEDULES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ScheduleManager] Error saving schedules.json ({e}).")


def save_user_schedule(user_id: int | str, schedule_dict: dict) -> dict:
    """
    Saves or overwrites a user's full weekly class schedule.
    schedule_dict format:
    {
      "Senin": [{"matkul": "...", "jam": "...", "ruang": "...", "dosen": "..."}, ...],
      "Selasa": [...],
      ...
    }
    """
    all_data = _load_all_schedules()
    u_key = str(user_id)

    # Standardize days structure
    standard_days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    formatted_schedule = {day: [] for day in standard_days}

    for day, items in schedule_dict.items():
        # Match day name case-insensitively
        matched_day = None
        for std_day in standard_days:
            if std_day.lower() in str(day).lower():
                matched_day = std_day
                break
        if matched_day and isinstance(items, list):
            formatted_schedule[matched_day] = items

    all_data[u_key] = formatted_schedule
    _save_all_schedules(all_data)
    return formatted_schedule


def get_user_schedule(user_id: int | str) -> dict:
    """Retrieves full weekly class schedule for a user."""
    all_data = _load_all_schedules()
    u_key = str(user_id)
    return all_data.get(u_key, {})


def get_daily_schedule(user_id: int | str, day_name: str = None) -> list:
    """
    Retrieves schedule items for a specific day.
    If day_name is None, defaults to current day of week in Indonesian.
    """
    if day_name is None:
        english_day = datetime.now().strftime("%A")
        day_name = DAYS_INDONESIA.get(english_day, "Senin")

    user_sched = get_user_schedule(user_id)
    for day_key, items in user_sched.items():
        if day_key.lower() == day_name.lower():
            return items
    return []


def clear_user_schedule(user_id: int | str) -> bool:
    """Clears all schedule data for a user."""
    all_data = _load_all_schedules()
    u_key = str(user_id)
    if u_key in all_data:
        del all_data[u_key]
        _save_all_schedules(all_data)
        return True
    return False
