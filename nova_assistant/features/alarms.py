import threading
import time
from datetime import datetime
from core.database import run_query


def add_alarm(time_str: str, label: str = "") -> str:
    if not time_str:
        return "What time should I set the alarm for?"
    run_query("INSERT INTO alarms (time_str, label) VALUES (?, ?)", (time_str, label))
    return f"Alarm set for {time_str}."


def list_alarms() -> str:
    rows = run_query("SELECT time_str FROM alarms WHERE active = 1", fetch=True)
    if not rows:
        return "You have no active alarms."
    times = ", ".join(r["time_str"] for r in rows)
    return f"Your alarms: {times}"


def start_alarm_watcher(tts, poll_seconds: int = 30):
    """
    Background thread: every poll_seconds, checks whether the current
    clock time (HH:MM) matches any stored alarm and speaks/announces it.
    NOTE: expects alarm times stored in "HH:MM" 24h format for exact
    matching; free-text times like "7 AM" should be normalized before
    insert in a production build.
    """
    def _loop():
        announced_this_minute = set()
        while True:
            now = datetime.now().strftime("%H:%M")
            rows = run_query(
                "SELECT id, time_str, label FROM alarms WHERE active = 1", fetch=True
            )
            for r in rows:
                if r["time_str"] == now and r["id"] not in announced_this_minute:
                    label = f" — {r['label']}" if r["label"] else ""
                    tts.say_async(f"Alarm{label}: it's {now}.")
                    announced_this_minute.add(r["id"])
            if now.endswith(":00"):
                announced_this_minute.clear()
            time.sleep(poll_seconds)

    threading.Thread(target=_loop, daemon=True).start()
