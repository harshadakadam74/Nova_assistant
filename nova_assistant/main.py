"""
Nova — Siri-style voice assistant.

Run on desktop:
    python main.py

Package for Android:
    buildozer -v android debug
"""

import threading
from math import sin, pi , cos

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from core.database import init_db
from core.text_to_speech import TextToSpeech
from core.speech_to_text import SpeechToText
from core.assistant import Nova
from core.wake_word import WakeWordListener

from features.alarms import start_alarm_watcher
from features.device_control import handle_device_command

from config import ASSISTANT_NAME


# ============================================================
# LOAD KV
# ============================================================

Builder.load_file("gui/nova.kv")


# ============================================================
# NOVA LISTENING ORB
# ============================================================

class NovaListeningOrb(Widget):

    phase = NumericProperty(0)
    rotation = NumericProperty(0)
    pulse = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bind(
            pos=self.draw_orb,
            size=self.draw_orb,
            phase=self.draw_orb,
            rotation=self.draw_orb,
            pulse=self.draw_orb,
        )

        # 60 FPS animation
        Clock.schedule_interval(self.animate, 1 / 60)

        self.draw_orb()

    # --------------------------------------------------------
    # Animation
    # --------------------------------------------------------

    def animate(self, dt):

        # Waveform movement
        self.phase += dt * 4.5

        # Ring rotation
        self.rotation += dt * 25

        # Center pulse
        self.pulse += dt * 3

        if self.rotation >= 360:
            self.rotation -= 360

        if self.pulse >= 2 * pi:
            self.pulse -= 2 * pi

    # --------------------------------------------------------
    # Draw complete orb
    # --------------------------------------------------------

    def draw_orb(self, *args):

        self.canvas.clear()

        cx = self.center_x
        cy = self.center_y

        with self.canvas:

            # ==================================================
            # OUTER BLUE GLOW
            # ==================================================

            Color(
                0.02,
                0.20,
                1.0,
                0.045
            )

            Ellipse(
                pos=(
                    cx - 160,
                    cy - 160
                ),
                size=(
                    320,
                    320
                )
            )

            # ==================================================
            # OUTER PURPLE GLOW
            # ==================================================

            Color(
                0.45,
                0.03,
                1.0,
                0.035
            )

            Ellipse(
                pos=(
                    cx - 145,
                    cy - 145
                ),
                size=(
                    290,
                    290
                )
            )

            # ==================================================
            # OUTER RING
            # ==================================================

            Color(
                0.02,
                0.35,
                1.0,
                0.45
            )

            Line(
                circle=(
                    cx,
                    cy,
                    142
                ),
                width=1
            )

            # ==================================================
            # SECOND RING
            # ==================================================

            Color(
                0.05,
                0.30,
                1.0,
                0.65
            )

            Line(
                circle=(
                    cx,
                    cy,
                    126
                ),
                width=1.3
            )

            # ==================================================
            # ROTATING BLUE RING
            # ==================================================

            Color(
                0.0,
                0.65,
                1.0,
                0.95
            )

            Line(
                ellipse=(
                    cx - 112,
                    cy - 112,
                    224,
                    224,
                    self.rotation,
                    self.rotation + 230
                ),
                width=2.2
            )

            # ==================================================
            # ROTATING PURPLE RING
            # ==================================================

            Color(
                0.65,
                0.05,
                1.0,
                0.95
            )

            Line(
                ellipse=(
                    cx - 112,
                    cy - 112,
                    224,
                    224,
                    self.rotation + 180,
                    self.rotation + 350
                ),
                width=2.2
            )

            # ==================================================
            # MAIN ORB GLOW
            # ==================================================

            Color(
                0.0,
                0.30,
                1.0,
                0.15
            )

            Ellipse(
                pos=(
                    cx - 88,
                    cy - 88
                ),
                size=(
                    176,
                    176
                )
            )

            # ==================================================
            # MAIN BLUE ORB
            # ==================================================

            Color(
                0.02,
                0.22,
                0.90,
                0.85
            )

            Ellipse(
                pos=(
                    cx - 67,
                    cy - 67
                ),
                size=(
                    134,
                    134
                )
            )

            # ==================================================
            # CYAN ORB
            # ==================================================

            Color(
                0.0,
                0.70,
                1.0,
                0.58
            )

            Ellipse(
                pos=(
                    cx - 63,
                    cy - 42
                ),
                size=(
                    92,
                    92
                )
            )

            # ==================================================
            # PURPLE ORB
            # ==================================================

            Color(
                0.75,
                0.03,
                1.0,
                0.58
            )

            Ellipse(
                pos=(
                    cx - 8,
                    cy - 48
                ),
                size=(
                    92,
                    92
                )
            )

            # ==================================================
            # BLUE LOWER ORB
            # ==================================================

            Color(
                0.05,
                0.35,
                1.0,
                0.58
            )

            Ellipse(
                pos=(
                    cx - 48,
                    cy - 64
                ),
                size=(
                    92,
                    92
                )
            )

            # ==================================================
            # CENTER LIGHT PULSE
            # ==================================================

            glow_size = 18 + sin(self.pulse) * 4

            Color(
                0.75,
                0.95,
                1.0,
                0.90
            )

            Ellipse(
                pos=(
                    cx - glow_size / 2,
                    cy - glow_size / 2
                ),
                size=(
                    glow_size,
                    glow_size
                )
            )

            # ==================================================
            # WAVEFORM
            # ==================================================

            self.draw_waveform(
                cx - 125,
                cy,
                -1
            )

            self.draw_waveform(
                cx + 125,
                cy,
                1
            )

    # --------------------------------------------------------
    # Waveform
    # --------------------------------------------------------

    def draw_waveform(self, x, y, direction):

        bars = 15
        spacing = 9

        for i in range(bars):

            wave = sin(
                self.phase * 2
                + i * 0.75
            )

            distance = abs(
                i - bars / 2
            )

            strength = max(
                0.15,
                1 - distance / 8
            )

            height = (
                10
                + strength * 52
                + wave * 9
            )

            height = max(
                5,
                height
            )

            if direction < 0:
                bar_x = x - i * spacing
            else:
                bar_x = x + i * spacing

            # Blue -> purple
            ratio = i / bars

            Color(
                ratio * 0.45,
                0.45 - ratio * 0.25,
                1.0,
                0.85
            )

            Line(
                points=[
                    bar_x,
                    y - height / 2,
                    bar_x,
                    y + height / 2,
                ],
                width=2
            )


# ============================================================
# NOVA ROOT
# ============================================================

class NovaRoot(BoxLayout):

    status_text = StringProperty(
        "Tap the mic and say something."
    )

    conversation_text = StringProperty("")

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        # ----------------------------------------------------
        # Initialize database
        # ----------------------------------------------------

        init_db()

        # ----------------------------------------------------
        # Core services
        # ----------------------------------------------------

        self.tts = TextToSpeech()

        self.stt = SpeechToText()

        self.nova = Nova(
            self.tts
        )

        self.wake_listener = WakeWordListener(
            self.stt,
            self._on_wake_word
        )

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        self._wake_active = False

        self._response_lock = threading.Lock()

        # ----------------------------------------------------
        # Alarm watcher
        # ----------------------------------------------------

        start_alarm_watcher(
            self.tts
        )

        # ----------------------------------------------------
        # Welcome message
        # ----------------------------------------------------

        self._append(
            f"{ASSISTANT_NAME}: "
            f"Hi! I'm {ASSISTANT_NAME}. "
            f"Tap the mic or say 'Hey Nova'."
        )

    # ========================================================
    # UI ACTIONS
    # ========================================================

    def on_mic_press(self):

        if self._response_lock.locked():
            return

        self.status_text = "Listening..."

        threading.Thread(
            target=self._listen_and_respond,
            daemon=True
        ).start()

    # --------------------------------------------------------

    def toggle_wake_word(self):

        if self._wake_active:

            self.wake_listener.stop()

            self._wake_active = False

            self.status_text = (
                "Wake-word listening stopped."
            )

        else:

            self.wake_listener.start()

            self._wake_active = True

            self.status_text = (
                f"Listening for "
                f"'Hey {ASSISTANT_NAME}'..."
            )

    # --------------------------------------------------------

    def clear_conversation(self):

        self.conversation_text = ""

    # ========================================================
    # WAKE WORD
    # ========================================================

    def _on_wake_word(self):

        Clock.schedule_once(
            lambda dt: self._append(
                f"{ASSISTANT_NAME}: Yes?"
            )
        )

        self.tts.say("Yes?")

        threading.Thread(
            target=self._listen_and_respond,
            daemon=True
        ).start()

    # ========================================================
    # PROCESS COMMAND
    # ========================================================

    def process_command(self, command):

        command = command.lower().strip()

        # ----------------------------------------------------
        # Device commands
        # ----------------------------------------------------

        response = handle_device_command(
            command
        )

        if response:

            Clock.schedule_once(
                lambda dt: self._append(
                    f"{ASSISTANT_NAME}: {response}"
                )
            )

            self.tts.say(response)

            return True

        # ----------------------------------------------------
        # Nova AI response
        # ----------------------------------------------------

        reply = self.nova.handle(
            command
        )

        Clock.schedule_once(
            lambda dt: self._append(
                f"{ASSISTANT_NAME}: {reply}"
            )
        )

        self.tts.say(reply)

        return True

    # ========================================================
    # LISTEN + RESPOND
    # ========================================================

    def _listen_and_respond(self):

        if not self._response_lock.acquire(
            blocking=False
        ):
            return

        try:

            # -----------------------------------------------
            # Listening
            # -----------------------------------------------

            Clock.schedule_once(
                lambda dt: setattr(
                    self,
                    "status_text",
                    "Listening..."
                )
            )

            heard = self.stt.listen_once()

            # -----------------------------------------------
            # Nothing heard
            # -----------------------------------------------

            if not heard:

                Clock.schedule_once(
                    lambda dt: setattr(
                        self,
                        "status_text",
                        "Didn't catch that — tap to try again."
                    )
                )

                return

            # -----------------------------------------------
            # User message
            # -----------------------------------------------

            Clock.schedule_once(
                lambda dt: self._append(
                    f"You: {heard}"
                )
            )

            # -----------------------------------------------
            # Processing
            # -----------------------------------------------

            Clock.schedule_once(
                lambda dt: setattr(
                    self,
                    "status_text",
                    "Thinking..."
                )
            )

            response = self.process_command(
                heard
            )

            # -----------------------------------------------
            # Finished
            # -----------------------------------------------

            if response:

                Clock.schedule_once(
                    lambda dt: setattr(
                        self,
                        "status_text",
                        "Tap the mic and say something."
                    )
                )

        except Exception as e:

            print(
                "Nova error:",
                e
            )

            Clock.schedule_once(
                lambda dt: setattr(
                    self,
                    "status_text",
                    "Something went wrong."
                )
            )

        finally:

            self._response_lock.release()

    # ========================================================
    # CHAT
    # ========================================================

    def _append(self, line: str):

        self.conversation_text += (
            line + "\n\n"
        )


# ============================================================
# NOVA APP
# ============================================================

class NovaApp(App):

    def build(self):

        self.title = (
            f"{ASSISTANT_NAME} — Voice Assistant"
        )

        return NovaRoot()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    NovaApp().run()