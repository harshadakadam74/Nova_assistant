from core.database import run_query


def add_note(content: str) -> str:
    if not content:
        return "What should I write down?"
    run_query("INSERT INTO notes (content) VALUES (?)", (content,))
    return "Noted."


def read_notes() -> str:
    rows = run_query("SELECT content FROM notes ORDER BY id DESC LIMIT 5", fetch=True)
    if not rows:
        return "You don't have any notes yet."
    return "Your recent notes: " + "; ".join(r["content"] for r in rows)
