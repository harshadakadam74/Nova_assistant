"""
Microphone capture + speech recognition. Uses Google's free web speech API
via SpeechRecognition (requires internet); swap `recognize_google` for
`recognize_vosk` or `recognize_sphinx` if you need fully offline STT.
"""
import sys
import threading

try:
    import distutils.version  # noqa: F401
except ModuleNotFoundError:
    import setuptools
    import setuptools._distutils as distutils

    sys.modules["distutils"] = distutils
    sys.modules["distutils.version"] = distutils.version

import speech_recognition as sr
from config import STT_LANGUAGE, STT_TIMEOUT, STT_PHRASE_LIMIT


class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.mic = sr.Microphone()
        self._mic_lock = threading.Lock()
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.6)

    def listen_once(self) -> str:
        """Blocks until it hears a phrase (or times out), returns lowercase text or ''."""
        with self._mic_lock:
            try:
                with self.mic as source:
                    audio = self.recognizer.listen(
                        source, timeout=STT_TIMEOUT, phrase_time_limit=STT_PHRASE_LIMIT
                    )
                text = self.recognizer.recognize_google(audio, language=STT_LANGUAGE)
                return text.lower().strip()
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                return ""
            except sr.RequestError as e:
                return f"__error__:{e}"

    def listen_for_wake_word(self, wake_words, timeout=None) -> bool:
        """Short listen cycle used in the background wake-word loop."""
        with self._mic_lock:
            try:
                with self.mic as source:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=3)
                text = self.recognizer.recognize_google(audio, language=STT_LANGUAGE).lower()
                return any(w in text for w in wake_words)
            except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError):
                return False
