import json
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DEADLINES_PATH = CONFIG_DIR / "deadlines.json"


def _load_all_deadlines() -> dict:
    """Reads config/deadlines.json."""
    if not DEADLINES_PATH.exists():
        return {}
    try:
        with open(DEADLINES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[DeadlineManager] Error reading deadlines.json ({e}).")
        return {}


def _save_all_deadlines(data: dict):
    """Writes config/deadlines.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(DEADLINES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[DeadlineManager] Error saving deadlines.json ({e}).")


def add_user_deadline(user_id: int | str, matkul: str, tugas: str, deadline_str: str) -> dict:
    """
    Adds a new deadline for a user.
    deadline_str format: "YYYY-MM-DD HH:MM"
    """
    all_data = _load_all_deadlines()
    u_key = str(user_id)

    user_list = all_data.get(u_key, [])
    item_id = f"dl_{int(time.time())}"

    new_item = {
        "id": item_id,
        "matkul": matkul.strip(),
        "tugas": tugas.strip(),
        "deadline": deadline_str.strip(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "reminded_24h": False,
        "reminded_3h": False
    }

    user_list.append(new_item)
    all_data[u_key] = user_list
    _save_all_deadlines(all_data)

    return new_item


def get_user_deadlines(user_id: int | str) -> list:
    """Retrieves all active deadlines for a user, sorted by deadline date."""
    all_data = _load_all_deadlines()
    u_key = str(user_id)
    user_list = all_data.get(u_key, [])

    # Filter out expired or sort active
    def parse_dt(d):
        try:
            return datetime.strptime(d["deadline"], "%Y-%m-%d %H:%M")
        except Exception:
            return datetime.max

    user_list.sort(key=parse_dt)
    return user_list


def delete_user_deadline(user_id: int | str, deadline_id: str) -> bool:
    """Deletes a specific deadline by ID."""
    all_data = _load_all_deadlines()
    u_key = str(user_id)
    user_list = all_data.get(u_key, [])

    initial_len = len(user_list)
    new_list = [d for d in user_list if d.get("id") != deadline_id]

    if len(new_list) < initial_len:
        all_data[u_key] = new_list
        _save_all_deadlines(all_data)
        return True
    return False


def get_all_active_deadlines() -> list:
    """Returns flat list of all active deadlines for all users with user_id attached."""
    all_data = _load_all_deadlines()
    result = []
    for user_id_str, d_list in all_data.items():
        for item in d_list:
            item_copy = dict(item)
            item_copy["user_id"] = user_id_str
            result.append(item_copy)
    return result


def mark_deadline_reminded(user_id: int | str, deadline_id: str, reminder_type: str):
    """
    Marks reminded_24h or reminded_3h as True.
    reminder_type: '24h' or '3h'
    """
    all_data = _load_all_deadlines()
    u_key = str(user_id)
    user_list = all_data.get(u_key, [])

    updated = False
    for d in user_list:
        if d.get("id") == deadline_id:
            if reminder_type == "24h":
                d["reminded_24h"] = True
            elif reminder_type == "3h":
                d["reminded_3h"] = True
            updated = True
            break

    if updated:
        all_data[u_key] = user_list
        _save_all_deadlines(all_data)
