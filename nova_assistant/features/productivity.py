"""Local tasks, schedule, approved preferences, and conversation history."""
from datetime import date, datetime, timedelta

from core.database import run_query


def add_task(text: str, due_date: str = "") -> str:
    text = text.strip()
    if not text:
        return "What should I add to your task list?"
    run_query("INSERT INTO tasks (text, due_date) VALUES (?, ?)", (text, due_date or None))
    return f"Added task: {text}."


def list_tasks() -> str:
    rows = run_query(
        "SELECT id, text, due_date FROM tasks WHERE done = 0 ORDER BY due_date, id LIMIT 20",
        fetch=True,
    )
    if not rows:
        return "Your task list is clear."
    return "Your tasks: " + "; ".join(
        f"{row['text']} (due {row['due_date']})" if row["due_date"] else row["text"]
        for row in rows
    )


def complete_task(task: str) -> str:
    task = task.strip()
    row = run_query(
        "SELECT id, text FROM tasks WHERE done = 0 AND "
        "(CAST(id AS TEXT) = ? OR LOWER(text) LIKE LOWER(?)) ORDER BY id LIMIT 1",
        (task, f"%{task}%"),
        fetchone=True,
    )
    if not row:
        return f"I couldn't find an open task matching {task}."
    run_query("UPDATE tasks SET done = 1 WHERE id = ?", (row["id"],))
    return f"Marked {row['text']} complete."


def add_schedule_event(title: str, event_date: str, event_time: str = "") -> str:
    title = title.strip()
    normalized_date = _normalize_date(event_date)
    if not title or normalized_date is None:
        return "Please give me an event name and a date such as today, tomorrow, or 2026-10-02."
    normalized_time = _normalize_time(event_time)
    if event_time and normalized_time is None:
        return "I couldn't understand that time. Try a time like 3 PM or 15:00."
    run_query(
        "INSERT INTO schedule_events (title, event_date, event_time) VALUES (?, ?, ?)",
        (title, normalized_date, normalized_time),
    )
    when = f" at {normalized_time}" if normalized_time else ""
    return f"Scheduled {title} for {normalized_date}{when}."


def schedule_for(event_date: str = "today") -> str:
    normalized_date = _normalize_date(event_date)
    if normalized_date is None:
        return "I couldn't understand that date."
    rows = run_query(
        "SELECT title, event_time FROM schedule_events WHERE event_date = ? "
        "ORDER BY event_time, id",
        (normalized_date,),
        fetch=True,
    )
    if not rows:
        return f"You have no scheduled events for {normalized_date}."
    items = [f"{row['event_time']} {row['title']}" if row["event_time"] else row["title"] for row in rows]
    return f"Your schedule for {normalized_date}: " + "; ".join(items)


def daily_briefing() -> str:
    today = date.today().isoformat()
    events = run_query(
        "SELECT title, event_time FROM schedule_events WHERE event_date = ? ORDER BY event_time",
        (today,),
        fetch=True,
    )
    tasks = run_query(
        "SELECT text FROM tasks WHERE done = 0 AND (due_date IS NULL OR due_date <= ?) "
        "ORDER BY due_date, id LIMIT 8",
        (today,),
        fetch=True,
    )
    reminders = run_query(
        "SELECT text, due_time FROM reminders WHERE done = 0 ORDER BY id DESC LIMIT 5",
        fetch=True,
    )
    sections = [f"Your briefing for {today}."]
    if events:
        sections.append("Schedule: " + "; ".join(
            f"{row['event_time']} {row['title']}" if row["event_time"] else row["title"]
            for row in events
        ))
    if tasks:
        sections.append("Tasks: " + "; ".join(row["text"] for row in tasks))
    if reminders:
        sections.append("Reminders: " + "; ".join(
            f"{row['text']} at {row['due_time']}" if row["due_time"] else row["text"]
            for row in reminders
        ))
    from config import OPENWEATHER_API_KEY
    if OPENWEATHER_API_KEY:
        from features.weather import get_weather
        sections.append("Weather: " + get_weather())
    from features.news import get_headlines
    headlines = get_headlines()
    if headlines:
        sections.append(headlines)
    if len(sections) == 1:
        sections.append("Your schedule and task list are clear today.")
    return " ".join(sections)


def remember_preference(preference: str) -> str:
    preference = preference.strip()
    if not preference:
        return "What preference would you like me to remember?"
    row = run_query("SELECT value FROM user_preferences WHERE key = 'profile'", fetchone=True)
    values = [item for item in (row["value"].splitlines() if row else []) if item]
    if preference.casefold() not in {value.casefold() for value in values}:
        values.append(preference)
    run_query(
        "INSERT INTO user_preferences (key, value) VALUES ('profile', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
        ("\n".join(values),),
    )
    return "I'll remember that preference."


def forget_preferences() -> str:
    run_query("DELETE FROM user_preferences WHERE key = 'profile'")
    return "I've forgotten your saved preferences."


def get_preferences() -> str:
    row = run_query("SELECT value FROM user_preferences WHERE key = 'profile'", fetchone=True)
    return row["value"] if row else ""


def set_setting(key: str, value: str) -> None:
    run_query(
        "INSERT INTO user_preferences (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
        (key, value),
    )


def get_setting(key: str, default: str = "") -> str:
    row = run_query("SELECT value FROM user_preferences WHERE key = ?", (key,), fetchone=True)
    return row["value"] if row else default


def save_conversation(role: str, content: str) -> None:
    if role in {"user", "assistant"} and content.strip():
        run_query(
            "INSERT INTO conversation_history (role, content) VALUES (?, ?)",
            (role, content.strip()),
        )


def search_conversation(query: str) -> str:
    query = query.strip()
    if not query:
        return "What should I search for in our conversation history?"
    rows = run_query(
        "SELECT role, content, created_at FROM conversation_history "
        "WHERE content LIKE ? ORDER BY id DESC LIMIT 10",
        (f"%{query}%",),
        fetch=True,
    )
    if not rows:
        return f"I couldn't find {query} in conversation history."
    return "Found: " + "; ".join(
        f"{row['created_at']} {row['role']}: {row['content']}" for row in rows
    )


def clear_conversation_history() -> None:
    run_query("DELETE FROM conversation_history")


def _normalize_date(value: str):
    value = value.strip().lower()
    if value == "today":
        return date.today().isoformat()
    if value == "tomorrow":
        return (date.today() + timedelta(days=1)).isoformat()
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def _normalize_time(value: str):
    value = value.strip().upper()
    if not value:
        return ""
    for pattern in ("%I:%M %p", "%I %p", "%H:%M"):
        try:
            return datetime.strptime(value, pattern).strftime("%H:%M")
        except ValueError:
            continue
    return None