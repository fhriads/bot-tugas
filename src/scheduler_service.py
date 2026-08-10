import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
from src.deadline_manager import get_all_active_deadlines, mark_deadline_reminded


async def _check_deadlines_job(application: Application):
    """
    Periodic job that checks active deadlines for all users and sends Gwis reminder notifications.
    """
    now = datetime.now()
    active_deadlines = get_all_active_deadlines()

    for item in active_deadlines:
        user_id_str = item.get("user_id")
        deadline_str = item.get("deadline", "")
        item_id = item.get("id")
        matkul = item.get("matkul", "Mata Kuliah")
        tugas = item.get("tugas", "Tugas")
        reminded_24h = item.get("reminded_24h", False)
        reminded_3h = item.get("reminded_3h", False)

        try:
            deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
        except Exception:
            continue

        time_diff = deadline_dt - now

        keyboard = [[InlineKeyboardButton("✅ Sudah Selesai", callback_data=f"dl_done:{item_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Check H-1 (24 Hours) threshold: between 23h and 24.5h remaining
        if timedelta(hours=23) <= time_diff <= timedelta(hours=24, minutes=30) and not reminded_24h:
            msg = (
                f"⏰ *Pengingat Deadline dari Gwis!* 🌸\n\n"
                f"• *Matkul:* {matkul}\n"
                f"• *Tugas:* {tugas}\n"
                f"• *Deadline:* `{deadline_dt.strftime('%d %B %Y jam %H:%M')}` (Besok!)\n\n"
                f"Jangan lupa dikerjakan ya! Gwis doakan lancar ngerjainnya ✨"
            )
            try:
                await application.bot.send_message(
                    chat_id=int(user_id_str),
                    text=msg,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                mark_deadline_reminded(user_id_str, item_id, "24h")
                print(f"[SchedulerService] Sent 24h reminder to user {user_id_str} for {matkul}")
            except Exception as e:
                print(f"[SchedulerService] Failed sending 24h notification ({e})")

        # Check 3 Hours threshold: between 2.5h and 3.5h remaining
        elif timedelta(hours=2, minutes=30) <= time_diff <= timedelta(hours=3, minutes=30) and not reminded_3h:
            msg = (
                f"⚠️ *Pengingat Penting dari Gwis (Tinggal 3 Jam)!* 🌸\n\n"
                f"• *Matkul:* {matkul}\n"
                f"• *Tugas:* {tugas}\n"
                f"• *Deadline:* `{deadline_dt.strftime('%H:%M WIB hari ini')}`\n\n"
                f"Yuk buruan diselesaikan dan dikirim tugasnya ya! 💪"
            )
            try:
                await application.bot.send_message(
                    chat_id=int(user_id_str),
                    text=msg,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                mark_deadline_reminded(user_id_str, item_id, "3h")
                print(f"[SchedulerService] Sent 3h reminder to user {user_id_str} for {matkul}")
            except Exception as e:
                print(f"[SchedulerService] Failed sending 3h notification ({e})")

        # Check Urgent / Immediate Test threshold: deadline within 10 minutes (or just past) and not reminded
        elif timedelta(minutes=-5) <= time_diff <= timedelta(minutes=10) and not (reminded_24h or reminded_3h):
            msg = (
                f"🚨 *Pengingat Urgent / Tes dari Gwis!* 🌸\n\n"
                f"• *Matkul:* {matkul}\n"
                f"• *Tugas:* {tugas}\n"
                f"• *Deadline:* `{deadline_dt.strftime('%H:%M WIB')}` (Sangat Dekat!)\n\n"
                f"Buruan diselesaikan dan dikirim tugasnya ya! Gwis bantu doakan! ✨"
            )
            try:
                await application.bot.send_message(
                    chat_id=int(user_id_str),
                    text=msg,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                mark_deadline_reminded(user_id_str, item_id, "3h")
                print(f"[SchedulerService] Sent urgent/test reminder to user {user_id_str} for {matkul}")
            except Exception as e:
                print(f"[SchedulerService] Failed sending urgent notification ({e})")


async def scheduler_loop(application: Application):
    """Background asyncio loop running every 60 seconds."""
    print("[SchedulerService] Gwis Deadline Reminder background scheduler started.")
    while True:
        try:
            await _check_deadlines_job(application)
        except Exception as e:
            print(f"[SchedulerService] Error in scheduler loop: {e}")
        await asyncio.sleep(60)


async def post_init_scheduler(application: Application):
    """Post initialization hook for ApplicationBuilder to start background scheduler."""
    asyncio.create_task(scheduler_loop(application))


def start_deadline_scheduler(application: Application):
    """Launches the background scheduler task when event loop is running."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(scheduler_loop(application))
    except RuntimeError:
        pass
