# Zyra — Siri-Style AI Voice Assistant (Python / Kivy)

Zyra is a mobile-first, voice-controlled AI assistant built in Python with a
touch UI (Kivy) so it can be packaged as an Android app (via Buildozer).

## Honest scope note (read this first)

A handful of Siri's abilities are literally impossible to replicate in pure
Python on a phone, so it's important to be upfront:

| Capability | Status |
|---|---|
| Wake word ("Hey Zyra"), voice commands, TTS replies | ✅ Real, working |
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
zyra_assistant/
├── main.py                 # Kivy app entry point, UI + orchestration
├── core/
│   ├── assistant.py         # Zyra brain: routes recognized text -> features
│   ├── speech_to_text.py    # Mic capture + recognition (Google/Vosk)
│   ├── text_to_speech.py    # Spoken replies (pyttsx3 offline / gTTS online)
│   ├── nlp_engine.py        # Intent + entity extraction (rule-based, extensible)
│   ├── ai_engine.py         # Optional Gemini chat fallback
│   └── wake_word.py         # Lightweight "Hey Zyra" wake-word loop
├── features/
│   ├── reminders.py         # Add/list/delete reminders (SQLite)
│   ├── alarms.py            # Set/cancel alarms, background trigger thread
│   ├── notes.py             # Voice notes / dictation storage
│   ├── timer_calc.py        # Countdown timers + spoken calculator
│   ├── weather.py           # Live weather via OpenWeatherMap API
│   ├── web_search.py        # Web search / "open <website>" / general Q&A
│   ├── news.py              # Bounded RSS headline summaries
│   ├── productivity.py      # Tasks, schedule, preferences, chat history
│   ├── device_control.py    # Volume/brightness/open-app (Android via plyer)
│   └── smalltalk.py         # Jokes, facts, greetings, fallback chat
├── data/
│   └── zyra.db               # SQLite storage (created on first run)
├── gui/
│   └── zyra.kv                # Kivy UI layout
├── config.py                 # API keys, settings
├── requirements.txt
└── buildozer.spec            # Android packaging config
```

## Setup (desktop, for development/testing)

```bash
pip install -r requirements.txt
python main.py
```

You'll need a working microphone. Speech recognition uses Google's web
recognition service, so recognized audio is sent to that service and internet
access is required. Zyra does not save microphone audio. Transcribed chat,
tasks, events, and preferences are stored locally in `data/zyra.db`; use
**Clear Chat** to delete the saved conversation history.

Optional services use environment variables rather than keys stored in source:

```powershell
$env:OPENWEATHER_API_KEY = "your-openweathermap-key"
$env:GEMINI_API_KEY = "your-gemini-key"
python main.py
```

Gemini is optional. Without `GEMINI_API_KEY`, local commands continue to work
and unmatched questions use Zyra's built-in fallback. Gemini receives the
current question, its short in-memory chat context, and only preferences the
user explicitly saved. It cannot invoke computer-control tools.

Use **Settings** to choose the recognition language, an installed system voice,
speech rate, theme, and either continuous listening or the “Hey Zyra” wake-word
mode. The microphone remains active while listening is enabled; use **Pause
Listening** to stop capture and **Stop Speech** to interrupt playback.

## Packaging for Android

```bash
pip install buildozer
buildozer -v android debug
```

This produces an installable `.apk`. First build takes a while (downloads
the Android SDK/NDK).

## Example voice commands Zyra understands

- "Hey Zyra"  → wakes it up
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
- "Add a task to review chapter two" / "Mark task review chapter two done"
- "Schedule study group on tomorrow at 3 PM" / "What's on my schedule tomorrow"
- "Give me my briefing" / "Start a pomodoro"
- "Remember that I prefer concise answers" / "Forget my preferences"
- "Search our conversation for notebook" / "Search files for report"
- "Explain recursion" / "Translate hello into Hindi" (Gemini key required)

## Extending it

All commands route through `core/nlp_engine.py`'s `parse_intent()`. To add a
new skill: add an intent pattern there, then add a handler function in
`core/assistant.py`'s `INTENT_HANDLERS` dict pointing at a new function in
`features/`.
