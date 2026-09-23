# Nova — Siri-Style AI Voice Assistant (Python / Kivy)

Nova is a mobile-first, voice-controlled AI assistant built in Python with a
touch UI (Kivy) so it can be packaged as an Android app (via Buildozer).

## Honest scope note (read this first)

A handful of Siri's abilities are literally impossible to replicate in pure
Python on a phone, so it's important to be upfront:

| Capability | Status |
|---|---|
| Wake word ("Hey Nova"), voice commands, TTS replies | ✅ Real, working |
| Reminders, alarms, notes, timers, calculator, jokes | ✅ Real, working (local SQLite) |
| Web search, "what's the weather", general Q&A | ✅ Real (needs internet + API keys) |
| Opening installed apps, adjusting volume/brightness | ✅ Real on **Android only**, via `plyer`/`jnius` |
| Making phone calls / sending SMS "as Siri does" | ⚠️ Real on Android with permissions granted; **not possible on iOS** — Apple does not allow any third-party app, Python or otherwise, to place calls or intercept system voice control. This is an OS restriction, not a code limitation. |
| Running as a system-wide assistant (double-press home / "Hey Siri" replacing Siri) | ❌ Not possible on iOS. Partially possible on Android (foreground service + wake word), included here. |

So: **this ships as a real installable Android app** with a genuine voice
assistant inside it. On iOS it will run as a normal in-app assistant (you
open the app and talk to it) but cannot replace or hook into Siri itself.

## Architecture

```
nova_assistant/
├── main.py                 # Kivy app entry point, UI + orchestration
├── core/
│   ├── assistant.py         # Nova brain: routes recognized text -> features
│   ├── speech_to_text.py    # Mic capture + recognition (Google/Vosk)
│   ├── text_to_speech.py    # Spoken replies (pyttsx3 offline / gTTS online)
│   ├── nlp_engine.py        # Intent + entity extraction (rule-based, extensible)
│   └── wake_word.py         # Lightweight "Hey Nova" wake-word loop
├── features/
│   ├── reminders.py         # Add/list/delete reminders (SQLite)
│   ├── alarms.py            # Set/cancel alarms, background trigger thread
│   ├── notes.py             # Voice notes / dictation storage
│   ├── timer_calc.py        # Countdown timers + spoken calculator
│   ├── weather.py           # Live weather via OpenWeatherMap API
│   ├── web_search.py        # Web search / "open <website>" / general Q&A
│   ├── device_control.py    # Volume/brightness/open-app (Android via plyer)
│   └── smalltalk.py         # Jokes, facts, greetings, fallback chat
├── data/
│   └── nova.db               # SQLite storage (created on first run)
├── gui/
│   └── nova.kv                # Kivy UI layout
├── config.py                 # API keys, settings
├── requirements.txt
└── buildozer.spec            # Android packaging config
```

## Setup (desktop, for development/testing)

```bash
pip install -r requirements.txt
python main.py
```

You'll need a working microphone. Set your OpenWeatherMap key (free tier is
fine) in `config.py` if you want live weather.

## Packaging for Android

```bash
pip install buildozer
buildozer -v android debug
```

This produces an installable `.apk`. First build takes a while (downloads
the Android SDK/NDK).

## Example voice commands Nova understands

- "Hey Nova"  → wakes it up
- "What time is it" / "What's today's date"
- "Set a reminder to call mom at 6 PM"
- "Set an alarm for 7 AM"
- "Take a note: buy groceries after work"
- "Set a timer for 10 minutes"
- "What's 45 times 12"
- "What's the weather in Mumbai"
- "Search the web for best pizza near me"
- "Open YouTube" / "Open camera" (Android)
- "Turn volume up" / "Turn brightness down" (Android)
- "Tell me a joke"
- "Stop listening" / "Goodbye"

## Extending it

All commands route through `core/nlp_engine.py`'s `parse_intent()`. To add a
new skill: add an intent pattern there, then add a handler function in
`core/assistant.py`'s `INTENT_HANDLERS` dict pointing at a new function in
`features/`.
