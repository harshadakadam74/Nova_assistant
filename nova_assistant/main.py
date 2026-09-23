"""
Nova — Siri-style voice assistant. Mobile app entry point (Kivy).

Run on desktop for development:   python main.py
Package for Android:              buildozer -v android debug
"""
import threading

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.lang import Builder

from core.database import init_db
from core.text_to_speech import TextToSpeech
from core.speech_to_text import SpeechToText
from core.assistant import Nova
from core.wake_word import WakeWordListener
from features.alarms import start_alarm_watcher
from config import ASSISTANT_NAME

Builder.load_file("gui/nova.kv")


class NovaRoot(BoxLayout):
    status_text = StringProperty("Tap the mic and say something.")
    conversation_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        init_db()
        self.tts = TextToSpeech()
        self.stt = SpeechToText()
        self.nova = Nova(self.tts)
        self.wake_listener = WakeWordListener(self.stt, self._on_wake_word)
        self._wake_active = False
        self._response_lock = threading.Lock()
        start_alarm_watcher(self.tts)
        self._append(f"{ASSISTANT_NAME}: Hi! I'm {ASSISTANT_NAME}. Tap the mic or say 'Hey Nova'.")

    # ---- UI actions ----
    def on_mic_press(self):
        if self._response_lock.locked():
            return
        self.status_text = "Listening..."
        threading.Thread(target=self._listen_and_respond, daemon=True).start()

    def toggle_wake_word(self):
        if self._wake_active:
            self.wake_listener.stop()
            self._wake_active = False
            self.status_text = "Wake-word listening stopped."
        else:
            self.wake_listener.start()
            self._wake_active = True
            self.status_text = f"Listening for 'Hey {ASSISTANT_NAME}'..."

    def clear_conversation(self):
        self.conversation_text = ""

    # ---- internal ----
    def _on_wake_word(self):
        Clock.schedule_once(lambda dt: self._append(f"{ASSISTANT_NAME}: Yes?"))
        self.tts.say(f"Yes?")
        self._listen_and_respond()

    def _listen_and_respond(self):
        if not self._response_lock.acquire(blocking=False):
            return
        try:
            heard = self.stt.listen_once()
            if not heard:
                Clock.schedule_once(lambda dt: setattr(self, "status_text", "Didn't catch that — tap to try again."))
                return

            Clock.schedule_once(lambda dt: self._append(f"You: {heard}"))
            reply = self.nova.handle(heard)
            Clock.schedule_once(lambda dt: self._append(f"{ASSISTANT_NAME}: {reply}"))
            Clock.schedule_once(lambda dt: setattr(self, "status_text", "Tap the mic and say something."))
            self.tts.say(reply)
        finally:
            self._response_lock.release()

    def _append(self, line: str):
        self.conversation_text += (line + "\n\n")


class NovaApp(App):
    def build(self):
        self.title = f"{ASSISTANT_NAME} — Voice Assistant"
        return NovaRoot()


if __name__ == "__main__":
    NovaApp().run()
