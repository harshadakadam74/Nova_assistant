"""Record 4 short phrases and save the authorized voiceprint to data/voiceprint.npy."""

from __future__ import annotations

import os

import numpy as np
import speech_recognition as sr

from core.voice_auth import VoiceAuthenticator

PHRASES = [
    "Hey Zyra",
    "Hey Zyra, open my computer",
    "Zyra, what is the time?",
    "Zyra, send a message",
]


def record_phrase(recognizer: sr.Recognizer, mic: sr.Microphone, prompt: str):
    print(f"\nSay: '{prompt}'")
    input("Press Enter when ready...\n")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.4)
        audio = recognizer.listen(source, timeout=8, phrase_time_limit=6)
    return audio


def main():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    auth = VoiceAuthenticator()

    enrollments = []
    for phrase in PHRASES:
        audio = record_phrase(recognizer, mic, phrase)
        raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        enrollments.append(samples)
        print(f"Recorded: {phrase} ({len(samples)} samples)")

    if not enrollments:
        raise RuntimeError("No recordings captured.")

    voiceprint_path = os.path.join(os.path.dirname(__file__), "data", "voiceprint.npy")
    auth.voiceprint_path = voiceprint_path
    auth.save_voiceprint(enrollments)
    print(f"Voiceprint saved at: {voiceprint_path}")


if __name__ == "__main__":
    main()
