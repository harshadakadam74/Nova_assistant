"""
Nova's "brain": takes recognized text, parses intent, dispatches to the
right feature handler, returns a spoken/displayed reply.
"""
from core.nlp_engine import parse_intent
from features import (
    reminders, alarms, notes, timer_calc, weather,
    web_search, device_control, smalltalk,
)


class Nova:
    def __init__(self, tts):
        self.tts = tts
        self.awake = False
        self.handlers = {
            "greeting": lambda e: smalltalk.greet(),
            "time_query": lambda e: smalltalk.current_time(),
            "date_query": lambda e: smalltalk.current_date(),

            "set_reminder": lambda e: reminders.add_reminder(e.get("task", ""), e.get("time", "")),
            "list_reminders": lambda e: reminders.list_reminders(),

            "set_alarm": lambda e: alarms.add_alarm(e.get("time", "")),
            "list_alarms": lambda e: alarms.list_alarms(),

            "take_note": lambda e: notes.add_note(e.get("content", "")),
            "read_notes": lambda e: notes.read_notes(),

            "set_timer": lambda e: timer_calc.start_timer(e.get("duration", ""), self.tts),
            "calculate": lambda e: timer_calc.calculate(e.get("expr", "")),

            "weather_query": lambda e: weather.get_weather(e.get("city", "")),

            "web_search": lambda e: web_search.search_web(e.get("query", "")),
            "open_website": lambda e: web_search.open_website(e.get("site", "")),
            "open_app": lambda e: device_control.open_app(f"open {e.get('app', '')}"),
            "device_control": lambda e: device_control.handle_device_command(e.get("command", "") or e.get("raw", "")),

            "volume_up": lambda e: device_control.volume_change("up"),
            "volume_down": lambda e: device_control.volume_change("down"),
            "brightness_up": lambda e: device_control.brightness_change("up"),
            "brightness_down": lambda e: device_control.brightness_change("down"),

            "tell_joke": lambda e: smalltalk.joke(),
            "tell_fact": lambda e: smalltalk.fact(),
            "thanks": lambda e: "You're welcome!",
            "stop_listening": lambda e: "Goodbye!",
        }

    def handle(self, text: str) -> str:
        """Takes raw recognized speech, returns Nova's reply text."""
        if not text:
            return ""
        if text.startswith("__error__:"):
            return "I'm having trouble reaching the speech recognition service."

        intent, entities = parse_intent(text)
        handler = self.handlers.get(intent)
        if handler:
            return handler(entities)
        return smalltalk.fallback(entities.get("raw", text))
