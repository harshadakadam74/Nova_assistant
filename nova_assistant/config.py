"""
Central configuration for Nova.
Fill in your own API keys below (or set as environment variables).
"""
import os

# --- Assistant identity ---
ASSISTANT_NAME = "Nova"
WAKE_WORDS = ["hey nova", "ok nova", "nova"]

# --- Speech ---
TTS_RATE = 175          # words per minute
TTS_VOICE_INDEX = 0     # 0 = default system voice; try 1 for an alt voice
STT_LANGUAGE = "en-IN"  # recognizer language/locale
STT_TIMEOUT = 6         # seconds to wait for speech to start
STT_PHRASE_LIMIT = 12   # max seconds of a single phrase

# --- Weather (https://openweathermap.org/api - free tier) ---
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
DEFAULT_CITY = "Latur"

# --- Storage ---
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "nova.db")

# --- Behavior ---
LISTEN_TIMEOUT_AFTER_WAKE = 5   # seconds of silence before Nova goes back to sleep
CONTINUOUS_WAKE_WORD_LISTENING = True  # keep listening for "Hey Nova" in background
