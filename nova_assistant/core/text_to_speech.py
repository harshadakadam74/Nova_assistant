"""
Offline text-to-speech via pyttsx3 (uses the OS's native TTS engine —
AVSpeechSynthesizer on iOS/macOS, SAPI5 on Windows, eSpeak/festival on
Linux/Android). No internet required, no API cost, low latency.
"""
import pyttsx3
import threading
from config import TTS_RATE, TTS_VOICE_INDEX


class TextToSpeech:
    def __init__(self):
        self._lock = threading.Lock()
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", TTS_RATE)
        voices = self.engine.getProperty("voices")
        if voices and 0 <= TTS_VOICE_INDEX < len(voices):
            self.engine.setProperty("voice", voices[TTS_VOICE_INDEX].id)

    def say(self, text: str):
        if not text:
            return
        with self._lock:
            self.engine.say(text)
            self.engine.runAndWait()

    def say_async(self, text: str):
        threading.Thread(target=self.say, args=(text,), daemon=True).start()
