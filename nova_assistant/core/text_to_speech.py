"""
Offline text-to-speech via pyttsx3 (uses the OS's native TTS engine —
AVSpeechSynthesizer on iOS/macOS, SAPI5 on Windows, eSpeak/festival on
Linux/Android). No internet required, no API cost, low latency.
"""
import os
import queue
import threading
import time

import pyttsx3
from config import TTS_RATE, TTS_VOICE_INDEX


class TextToSpeech:
    def __init__(self):
        self._commands = queue.Queue()
        self._ready = threading.Event()
        self._startup_error = None
        self._interrupt_requested = threading.Event()
        self.voice_options = []
        self.current_voice_id = None
        self.current_rate = TTS_RATE
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait()
        if self._startup_error:
            raise RuntimeError("Could not initialize text-to-speech") from self._startup_error

    def say(self, text: str):
        if not text:
            return
        completed = threading.Event()
        errors = []
        self._commands.put(("speak", text, completed, errors))
        completed.wait()
        if errors:
            raise errors[0]

    def say_async(self, text: str):
        if text:
            self._commands.put(("speak", text, None, None))

    def stop(self):
        self._interrupt_requested.set()

    def set_voice(self, voice_id):
        if voice_id not in {voice_id for voice_id, _ in self.voice_options}:
            return False
        completed = threading.Event()
        errors = []
        self._commands.put(("voice", voice_id, completed, errors))
        completed.wait()
        if errors:
            raise errors[0]
        self.current_voice_id = voice_id
        return True

    def set_rate(self, rate):
        rate = max(100, min(250, int(rate)))
        completed = threading.Event()
        errors = []
        self._commands.put(("rate", rate, completed, errors))
        completed.wait()
        if errors:
            raise errors[0]
        self.current_rate = rate
        return True

    def _run(self):
        comtypes = None
        try:
            if os.name == "nt":
                import comtypes
                comtypes.CoInitialize()

            engine = pyttsx3.init()
            engine.setProperty("rate", TTS_RATE)
            voices = engine.getProperty("voices")
            self.voice_options = [
                (voice.id, str(voice.name)) for voice in (voices or [])
            ]
            if voices and 0 <= TTS_VOICE_INDEX < len(voices):
                self.current_voice_id = voices[TTS_VOICE_INDEX].id
                engine.setProperty("voice", self.current_voice_id)
        except Exception as error:
            self._startup_error = error
            self._ready.set()
            if comtypes is not None:
                comtypes.CoUninitialize()
            return

        self._ready.set()
        try:
            while True:
                operation, value, completed, errors = self._commands.get()
                if operation == "close":
                    break
                try:
                    if operation == "voice":
                        engine.setProperty("voice", value)
                    elif operation == "rate":
                        engine.setProperty("rate", value)
                    else:
                        self._speak(engine, value)
                except Exception as error:
                    if errors is not None:
                        errors.append(error)
                finally:
                    if completed is not None:
                        completed.set()
        finally:
            engine.stop()
            if comtypes is not None:
                comtypes.CoUninitialize()

    def _speak(self, engine, text):
        self._interrupt_requested.clear()
        engine.say(text)
        engine.startLoop(False)
        try:
            while engine.isBusy():
                if self._interrupt_requested.is_set():
                    engine.stop()
                    break
                engine.iterate()
                time.sleep(0.01)
        finally:
            engine.endLoop()
            self._interrupt_requested.clear()
            