"""
Central configuration for Zyra.
Fill in your own API keys below (or set as environment variables).
"""
import os

# --- Assistant identity ---
ASSISTANT_NAME = "Zyra"
WAKE_WORDS = ["hey zyra", "ok zyra", "zyra"]

# --- Speech ---
TTS_RATE = 175          # words per minute
TTS_VOICE_INDEX = 0     # 0 = default system voice; try 1 for an alt voice
STT_LANGUAGE = "en-IN"  # recognizer language/locale
STT_LANGUAGE_OPTIONS = {
	"English (India)": "en-IN",
	"English (US)": "en-US",
	"Hindi": "hi-IN",
	"Marathi": "mr-IN",
}
STT_TIMEOUT = 6         # seconds to wait for speech to start
STT_PHRASE_LIMIT = 12   # max seconds of a single phrase

# --- Weather (https://openweathermap.org/api - free tier) ---
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
DEFAULT_CITY = "Latur"

# --- Optional conversational AI ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_TIMEOUT = 15
GEMINI_HISTORY_TURNS = 6

# --- Storage ---
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "zyra.db")

# --- Behavior ---
LISTEN_TIMEOUT_AFTER_WAKE = 5   # seconds of silence before Zyra goes back to sleep
CONTINUOUS_WAKE_WORD_LISTENING = True  # keep listening for "Hey Zyra" in background
