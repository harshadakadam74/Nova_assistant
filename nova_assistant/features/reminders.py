from core.database import run_query


def add_reminder(task: str, time_str: str = "") -> str:
    if not task:
        return "What should I remind you about?"
    run_query(
        "INSERT INTO reminders (text, due_time) VALUES (?, ?)",
        (task, time_str),
    )
    if time_str:
        return f"Got it. I'll remind you to {task} at {time_str}."
    return f"Got it. I'll remind you to {task}."


def list_reminders() -> str:
    rows = run_query(
        "SELECT text, due_time FROM reminders WHERE done = 0 ORDER BY id DESC LIMIT 10",
        fetch=True,
    )
    if not rows:
        return "You don't have any reminders."
    parts = []
    for r in rows:
        if r["due_time"]:
            parts.append(f"{r['text']} at {r['due_time']}")
        else:
            parts.append(r["text"])
    return "Your reminders: " + "; ".join(parts)
