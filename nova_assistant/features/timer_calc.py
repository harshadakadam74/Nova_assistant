import re
import threading
import time


def start_timer(duration_str: str, tts, on_tick=None) -> str:
    seconds = _parse_duration(duration_str)
    if seconds is None:
        return "I didn't catch how long to set the timer for."

    def _run():
        time.sleep(seconds)
        tts.say_async("Time's up!")

    threading.Thread(target=_run, daemon=True).start()
    return f"Timer set for {duration_str}."


def _parse_duration(text: str):
    text = text.lower()
    total = 0
    for value, unit in re.findall(r"(\d+)\s*(hour|hr|minute|min|second|sec)", text):
        value = int(value)
        if unit.startswith("hour") or unit == "hr":
            total += value * 3600
        elif unit.startswith("min"):
            total += value * 60
        else:
            total += value
    return total if total > 0 else None


_ALLOWED = set("0123456789+-*/. ()")


def calculate(expr: str) -> str:
    if not expr or not set(expr) <= _ALLOWED:
        return "I can only do simple math like addition, subtraction, multiplication and division."
    try:
        result = eval(expr, {"__builtins__": {}}, {})  # restricted eval, digits/operators only
        return f"That's {result}."
    except Exception:
        return "Sorry, I couldn't calculate that."
