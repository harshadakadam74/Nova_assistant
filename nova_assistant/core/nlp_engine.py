"""
Rule-based intent recognizer. Not a neural NLU model — but fast, offline,
fully predictable, and easy to extend, which matters more than raw
sophistication for a voice assistant with a fixed skill set.

parse_intent(text) -> (intent_name: str, entities: dict)
"""
import re

# Each entry: (intent_name, [regex patterns], entity_extractor_or_None)
_PATTERNS = [
    ("greeting", [r"\b(hi|hello|hey)\b(?!.*nova)"], None),
    ("time_query", [r"\bwhat.?s the time\b", r"\bwhat time is it\b"], None),
    ("date_query", [r"\bwhat.?s (today.?s )?date\b", r"\bwhat day is it\b"], None),

    ("set_reminder", [r"\bremind me to (?P<task>.+?)(?: at (?P<time>.+))?$",
                       r"\bset a reminder to (?P<task>.+?)(?: at (?P<time>.+))?$"], "reminder"),
    ("list_reminders", [r"\bwhat are my reminders\b", r"\blist my reminders\b"], None),

    ("set_alarm", [r"\bset an? alarm for (?P<time>.+)$", r"\bwake me up at (?P<time>.+)$"], "alarm"),
    ("list_alarms", [r"\blist my alarms\b", r"\bwhat alarms\b"], None),

    ("take_note", [r"\btake a note[:,]? (?P<content>.+)$", r"\bnote that (?P<content>.+)$"], "note"),
    ("read_notes", [r"\bread my notes\b", r"\bwhat are my notes\b"], None),

    ("set_timer", [r"\bset a timer for (?P<duration>.+)$"], "timer"),

    ("calculate", [r"\bwhat.?s (?P<expr>[\d\s\.\+\-\*\/xX×÷plus minus times dividedby]+)\??$",
                    r"\bcalculate (?P<expr>.+)$"], "calc"),

    ("weather_query", [r"\bweather\b(?: in (?P<city>[a-zA-Z\s]+))?"], "weather"),

    ("web_search", [r"\bsearch (?:the web )?for (?P<query>.+)$",
                     r"\bgoogle (?P<query>.+)$"], "search"),
    ("open_website", [r"\bopen (?P<site>[\w\.\-]+\.(com|org|in|net))\b"], "website"),
    ("open_app", [r"\bopen (?P<app>.+?)(?: app)?$"], "app"),

    ("volume_up", [r"\b(turn |increase )?volume up\b", r"\bincrease the volume\b"], None),
    ("volume_down", [r"\b(turn |decrease )?volume down\b", r"\bdecrease the volume\b"], None),
    ("brightness_up", [r"\bbrightness up\b", r"\bincrease brightness\b"], None),
    ("brightness_down", [r"\bbrightness down\b", r"\bdecrease brightness\b"], None),

    ("tell_joke", [r"\btell me a joke\b", r"\bmake me laugh\b"], None),
    ("tell_fact", [r"\btell me a fact\b", r"\brandom fact\b"], None),

    ("stop_listening", [r"\bstop listening\b", r"\bgoodbye\b", r"\bstop nova\b", r"\bgo to sleep\b"], None),
    ("thanks", [r"\bthank(s| you)\b"], None),
]

_NUM_WORDS = {"plus": "+", "minus": "-", "times": "*", "x": "*", "×": "*", "dividedby": "/", "÷": "/"}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\.\:\+\-\*\/×÷]", "", text)
    return text


def parse_intent(text: str):
    """Returns (intent, entities_dict). Falls back to ('unknown', {'raw': text})."""
    norm = _normalize(text)
    for intent, patterns, kind in _PATTERNS:
        for pat in patterns:
            m = re.search(pat, norm)
            if m:
                entities = m.groupdict() if m.groupdict() else {}
                entities = {k: v.strip() for k, v in entities.items() if v}
                if kind == "calc" and "expr" in entities:
                    entities["expr"] = _words_to_symbols(entities["expr"])
                return intent, entities
    return "unknown", {"raw": text}


def _words_to_symbols(expr: str) -> str:
    for word, symbol in _NUM_WORDS.items():
        expr = expr.replace(f" {word} ", f" {symbol} ")
    return expr
