"""
Zyra — Siri-style voice assistant.

Run on desktop:
    python main.py

Package for Android:
    buildozer -v android debug
"""

import threading
import sys
from datetime import datetime
import psutil
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

from core.database import init_db
from core.text_to_speech import TextToSpeech
from core.speech_to_text import SpeechToText
from core.assistant import Zyra
from features.alarms import start_alarm_watcher
from features.device_control import handle_device_command
from features import productivity


from config import (
    ASSISTANT_NAME,
    STT_LANGUAGE,
    STT_LANGUAGE_OPTIONS,
    STT_RETRY_DELAY,
    TTS_RATE,
    WAKE_WORDS,
    ZYRA_COLORS,
)

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None


# ============================================================
# LOAD KV
# ============================================================

Builder.load_file("gui/zyra.kv")


# ============================================================
# ZYRA LISTENING ORB
# ============================================================

class ZyraListeningOrb(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.draw_orb,
            size=self.draw_orb,
        )
        self.draw_orb()

    def draw_orb(self, *args):
        self.canvas.clear()
        cx = self.center_x
        cy = self.center_y
        with self.canvas:
            Color(0.02, 0.20, 1.0, 0.08)
            Ellipse(pos=(cx - 145, cy - 145), size=(290, 290))
            Color(0.02, 0.35, 1.0, 0.55)
            Line(circle=(cx, cy, 142), width=1)
            Color(0.0, 0.65, 1.0, 0.95)
            Line(ellipse=(cx - 112, cy - 112, 224, 224, 25, 255), width=2.2)
            Color(0.65, 0.05, 1.0, 0.9)
            Line(ellipse=(cx - 112, cy - 112, 224, 224, 200, 350), width=2.2)
            Color(0.02, 0.22, 0.90, 0.85)
            Ellipse(pos=(cx - 67, cy - 67), size=(134, 134))
            Color(0.0, 0.70, 1.0, 0.58)
            Ellipse(pos=(cx - 63, cy - 42), size=(92, 92))
            Color(0.75, 0.03, 1.0, 0.58)
            Ellipse(pos=(cx - 8, cy - 48), size=(92, 92))
            Color(0.75, 0.95, 1.0, 0.95)
            Ellipse(pos=(cx - 9, cy - 9), size=(18, 18))


class ZyraSettingsPopup(Popup):

    assistant_root = ObjectProperty(None, allownone=True)
    language_labels = ListProperty(list(STT_LANGUAGE_OPTIONS))
    voice_labels = ListProperty([])
    selected_language = StringProperty("English (India)")
    selected_voice = StringProperty("System default")
    selected_theme = StringProperty("Dark")
    selected_mode = StringProperty("Always listening")
    rate = NumericProperty(TTS_RATE)

    def __init__(self, assistant_root, **kwargs):
        super().__init__(**kwargs)
        self.assistant_root = assistant_root
        self._voice_by_label = {}

    def apply_settings(self):
        root = self.assistant_root
        language = STT_LANGUAGE_OPTIONS.get(self.ids.language_spinner.text)
        if language and root.stt:
            root.stt.set_language(language)
            if root.database_available:
                productivity.set_setting("language", language)

        voice_id = self._voice_by_label.get(self.ids.voice_spinner.text)
        rate = int(self.ids.rate_slider.value)
        if root.database_available:
            if voice_id:
                productivity.set_setting("voice_id", voice_id)
            productivity.set_setting("tts_rate", str(rate))
        root.set_theme(self.ids.theme_spinner.text, persist=root.database_available)
        root.set_listening_mode(self.ids.mode_spinner.text)
        self.dismiss()

        def apply_tts_settings():
            try:
                if voice_id:
                    root.tts.set_voice(voice_id)
                root.tts.set_rate(rate)
            except Exception as error:
                Clock.schedule_once(
                    lambda dt: root._append(f"Speech setting error: {error}")
                )

        threading.Thread(target=apply_tts_settings, daemon=True).start()


# ============================================================
# ZYRA ROOT
# ============================================================

class _UnavailableTextToSpeech:

    voice_options = []
    current_voice_id = None

    def say(self, text):
        return

    def say_async(self, text):
        return

    def stop(self):
        return

    def set_voice(self, voice_id):
        return False

    def set_rate(self, rate):
        return False


class ZyraRoot(BoxLayout):

    status_text = StringProperty(
        "I'm listening..."
    )

    conversation_text = StringProperty("")
    auto_listening = BooleanProperty(False)
    listening_mode = StringProperty("Always listening")
    theme = StringProperty("Dark")
    background_color = ListProperty([0.008, 0.035, 0.12, 1])
    surface_color = ListProperty([0.065, 0.095, 0.185, 1])
    border_color = ListProperty([0.172, 0.240, 0.420, 1])
    primary_text_color = ListProperty([0.906, 0.925, 0.969, 1])
    secondary_text_color = ListProperty([0.557, 0.616, 0.757, 1])
    cpu_status = StringProperty("CPU --")
    memory_status = StringProperty("RAM --")
    battery_status = StringProperty("BATTERY --")

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        startup_errors = []
        self.database_available = False

        try:
            init_db()
            self.database_available = True
        except Exception as error:
            startup_errors.append(f"Database: {error}")

        try:
            self.tts = TextToSpeech()
            tts_available = True
        except Exception as error:
            self.tts = _UnavailableTextToSpeech()
            tts_available = False
            startup_errors.append(f"Text-to-speech: {error}")

        try:
            self.stt = SpeechToText()
        except Exception as error:
            self.stt = None
            startup_errors.append(f"Microphone: {error}")

        self.zyra = Zyra(
            self.tts
        )

        self._response_lock = threading.Lock()
        self._auto_thread = None
        self._wake_triggered = False

        language = (
            productivity.get_setting("language", STT_LANGUAGE)
            if self.database_available else STT_LANGUAGE
        )
        if self.stt:
            self.stt.set_language(language)
        self.listening_mode = (
            productivity.get_setting("listening_mode", "Always listening")
            if self.database_available else "Always listening"
        )
        saved_theme = productivity.get_setting("theme", "Dark") if self.database_available else "Dark"
        self.set_theme(saved_theme, persist=False)
        self._apply_saved_voice_settings()
        self.refresh_system_status(0)
        Clock.schedule_interval(self.refresh_system_status, 5)

        # ----------------------------------------------------
        # Alarm watcher
        # ----------------------------------------------------

        if tts_available:
            try:
                start_alarm_watcher(self.tts)
            except Exception as error:
                startup_errors.append(f"Alarm watcher: {error}")

        # ----------------------------------------------------
        # Welcome message
        # ----------------------------------------------------

        self._append(
            f"{ASSISTANT_NAME}: "
            f"Hi! I'm {ASSISTANT_NAME}. "
            "I'm listening. Speak naturally."
        )

        if startup_errors:
            self.status_text = "Startup issue. See chat for details."
            for error in startup_errors:
                self._append(f"Startup error: {error}")

        if self.stt is not None:
            Clock.schedule_once(self.start_auto_listening, 1)

    # ========================================================
    # UI ACTIONS
    # ========================================================

    def start_auto_listening(self, *args):
        if self.stt is None:
            self.status_text = "Microphone unavailable. See chat for details."
            return

        if self._auto_thread and self._auto_thread.is_alive():
            self.auto_listening = True
            self.status_text = "Listening..."
            return

        self.auto_listening = True
        self.status_text = "Listening..."
        self._auto_thread = threading.Thread(
            target=self._auto_listen_loop,
            daemon=True,
        )
        self._auto_thread.start()

    def stop_auto_listening(self):
        self.auto_listening = False
        self.status_text = "Pausing listening..."
        self.tts.stop()

    def toggle_auto_listening(self):
        if self.auto_listening:
            self.stop_auto_listening()
        else:
            self.start_auto_listening()

    def set_listening_mode(self, mode):
        if mode not in {"Always listening", "Hey Zyra"}:
            return
        self.listening_mode = mode
        self._wake_triggered = False
        if self.database_available:
            productivity.set_setting("listening_mode", mode)
        if self.auto_listening:
            self.status_text = "Listening..." if mode == "Always listening" else "Listening for Hey Zyra..."

    def set_theme(self, theme, persist=True):
        if theme == "Light":
            self.background_color = [0.94, 0.96, 0.98, 1]
            self.surface_color = [1, 1, 1, 1]
            self.border_color = [0.72, 0.78, 0.86, 1]
            self.primary_text_color = [0.10, 0.14, 0.22, 1]
            self.secondary_text_color = [0.29, 0.35, 0.45, 1]
            self.theme = "Light"
        else:
            self.background_color = [0.008, 0.035, 0.12, 1]
            self.surface_color = [0.065, 0.095, 0.185, 1]
            self.border_color = [0.172, 0.240, 0.420, 1]
            self.primary_text_color = [0.906, 0.925, 0.969, 1]
            self.secondary_text_color = [0.557, 0.616, 0.757, 1]
            self.theme = "Dark"
        if persist and self.database_available:
            productivity.set_setting("theme", self.theme)

    def open_settings(self):
        popup = ZyraSettingsPopup(self)
        popup.selected_language = next(
            (label for label, code in STT_LANGUAGE_OPTIONS.items()
             if self.stt and code == self.stt.language),
            "English (India)",
        )
        popup.selected_theme = self.theme
        popup.selected_mode = self.listening_mode
        popup.rate = getattr(self.tts, "current_rate", TTS_RATE)

        for index, (voice_id, voice_name) in enumerate(getattr(self.tts, "voice_options", []), 1):
            label = f"{voice_name} ({index})"
            popup.voice_labels.append(label)
            popup._voice_by_label[label] = voice_id
            if voice_id == getattr(self.tts, "current_voice_id", None):
                popup.selected_voice = label

        if not popup.voice_labels:
            popup.voice_labels = ["System default"]
        popup.open()

    def _apply_saved_voice_settings(self):
        if not self.database_available:
            return
        rate = productivity.get_setting("tts_rate", str(TTS_RATE))
        try:
            self.tts.set_rate(int(rate))
        except (AttributeError, ValueError, RuntimeError):
            pass
        voice_id = productivity.get_setting("voice_id")
        if voice_id:
            try:
                self.tts.set_voice(voice_id)
            except (AttributeError, RuntimeError):
                pass

    def refresh_system_status(self, *_args):
        self.cpu_status = f"CPU {psutil.cpu_percent(interval=None):.0f}%"
        self.memory_status = f"RAM {psutil.virtual_memory().percent:.0f}%"
        try:
            battery = psutil.sensors_battery()
        except (OSError, RuntimeError):
            battery = None
        self.battery_status = (
            f"BATTERY {battery.percent:.0f}%" if battery else "BATTERY N/A"
        )

    def stop_speech(self):
        self.tts.stop()
        self.status_text = "Speech stopped."

    def clear_conversation(self):

        self.conversation_text = ""
        if self.database_available:
            productivity.clear_conversation_history()

    # ========================================================
    # AUTOMATIC LISTENING
    # ========================================================

    def _auto_listen_loop(self):
        while self.auto_listening:
            if not self._response_lock.acquire(timeout=0.25):
                continue

            try:
                if not self.auto_listening:
                    break

                if self.listening_mode == "Hey Zyra" and not self._wake_triggered:
                    detected = self.stt.listen_for_wake_word(WAKE_WORDS, timeout=4)
                    if detected:
                        self._wake_triggered = True
                        Clock.schedule_once(
                            lambda dt: setattr(self, "status_text", "Speak your command...")
                        )
                        self.tts.say("Yes?")
                    continue

                Clock.schedule_once(
                    lambda dt: setattr(self, "status_text", "Listening...")
                )
                heard = self.stt.listen_once()
                if not self.auto_listening:
                    break
                if heard.startswith("__error__:"):
                    Clock.schedule_once(
                        lambda dt: setattr(
                            self,
                            "status_text",
                            "Speech service unavailable; retrying...",
                        )
                    )
                    threading.Event().wait(STT_RETRY_DELAY)
                    continue
                if not heard:
                    if self.listening_mode == "Hey Zyra":
                        self._wake_triggered = False
                    continue

                self._record_message("user", heard)
                Clock.schedule_once(
                    lambda dt: setattr(self, "status_text", "Thinking...")
                )

                self.process_command(heard, wait_for_speech=True)
                self._wake_triggered = False

                if self.auto_listening:
                    Clock.schedule_once(
                        lambda dt: setattr(
                            self,
                            "status_text",
                            "Listening..." if self.listening_mode == "Always listening" else "Listening for Hey Zyra...",
                        )
                    )
            except Exception as error:
                print("Automatic listening error:", error)
                Clock.schedule_once(
                    lambda dt: setattr(
                        self,
                        "status_text",
                        "Listening paused briefly after an error...",
                    )
                )
                threading.Event().wait(1)
            finally:
                self._response_lock.release()

    # ========================================================
    # PROCESS COMMAND
    # ========================================================

    def process_command(self, command, wait_for_speech=False):

        command = command.lower().strip()

        if command in {"stop listening", "goodbye", "stop zyra", "go to sleep"}:
            self.stop_auto_listening()
            self._deliver_response(
                "Listening paused. Zyra will stay open; tap Start Listening to resume.",
                wait_for_speech,
            )
            self.status_text = "Listening paused. Zyra is still open."
            return True

        if command in {"stop speaking", "be quiet"}:
            self.tts.stop()
            self._record_message("assistant", "Stopped speaking.")
            return True

        # ----------------------------------------------------
        # Device commands
        # ----------------------------------------------------

        response = handle_device_command(
            command
        )

        if response:
            self._deliver_response(response, wait_for_speech)
            return True

        # ----------------------------------------------------
        # Zyra AI response
        # ----------------------------------------------------

        reply = self.zyra.handle(
            command
        )

        self._deliver_response(reply, wait_for_speech)
        return True

    def _deliver_response(self, response, wait_for_speech):
        self._record_message("assistant", response)

        if wait_for_speech:
            Clock.schedule_once(
                lambda dt: setattr(self, "status_text", "Speaking...")
            )
            self.tts.say(response)
        else:
            self.tts.say_async(response)

    def _record_message(self, role, content):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.database_available:
            productivity.save_conversation(role, content)
        label = "You" if role == "user" else ASSISTANT_NAME
        Clock.schedule_once(
            lambda dt: self._append(f"[{timestamp}] {label}: {content}")
        )

    # ========================================================
    # CHAT
    # ========================================================

    def _append(self, line: str):

        self.conversation_text += (
            line + "\n\n"
        )


# ============================================================
# ZYRA APP
# ============================================================

class ZyraApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tray_icon = None
        self._quitting = False

    def build(self):

        self.title = (
            f"{ASSISTANT_NAME} — Voice Assistant"
        )

        Window.bind(on_request_close=self._handle_window_close)
        return ZyraRoot()

    def on_start(self):
        if sys.platform != "win32" or pystray is None:
            return

        image = Image.new("RGBA", (64, 64), (15, 22, 40, 255))
        draw = ImageDraw.Draw(image)
        draw.ellipse((7, 7, 57, 57), fill=(33, 102, 168, 255), outline=(84, 185, 255, 255), width=3)
        draw.ellipse((27, 27, 37, 37), fill=(255, 255, 255, 255))
        menu = pystray.Menu(
            pystray.MenuItem("Show Zyra", self._show_from_tray, default=True),
            pystray.MenuItem("Quit Zyra", self._quit_from_tray),
        )
        self._tray_icon = pystray.Icon("zyra", image, "Zyra assistant", menu)
        threading.Thread(target=self._tray_icon.run, daemon=True).start()

    def _handle_window_close(self, *_args):
        if sys.platform == "win32" and self._tray_icon and not self._quitting:
            Window.hide()
            if self.root:
                self.root.status_text = "Zyra is running in the system tray."
            return True
        return False

    def _show_from_tray(self, *_args):
        Clock.schedule_once(self._restore_window)

    def _restore_window(self, _dt):
        Window.show()
        Window.restore()
        Window.raise_window()

    def _quit_from_tray(self, *_args):
        Clock.schedule_once(self._quit_app)

    def _quit_app(self, _dt):
        self._quitting = True
        self.stop()

    def on_stop(self):
        if self.root:
            self.root.stop_auto_listening()
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    ZyraApp().run()