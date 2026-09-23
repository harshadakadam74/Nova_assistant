"""
Background thread that keeps listening (in short bursts) for a wake word
like "Hey Nova". This is a simple always-listening loop built on the same
STT engine — not a dedicated low-power wake-word model (e.g. Porcupine),
but it works without extra native dependencies or licensing.
"""
import threading
import time
from config import WAKE_WORDS


class WakeWordListener:
    def __init__(self, stt, on_wake_callback):
        self.stt = stt
        self.on_wake = on_wake_callback
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                heard = self.stt.listen_for_wake_word(WAKE_WORDS, timeout=4)
                if heard:
                    self.on_wake()
            except Exception:
                time.sleep(0.5)
                continue
