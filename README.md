# J.A.R.V.I.S. AI Voice Assistant

A hands-free, Windows-focused personal assistant built with Python. Talk to
it (wake word: "Hey Jarvis"), and it will answer questions using Groq,
control your PC, manage files, play media, and even write code for you.

Two ways to run it:
- `python jarvis.py` — a terminal, fully hands-free, wake-word driven engine.
- `streamlit run app.py` — a browser-based chat UI with a mic button.

Both share the exact same brain (`core/command_handler.py`), so they behave
identically.

## Features

- **Wake word + continuous listening** — say "Hey Jarvis" and keep talking,
  no button presses needed (terminal mode).
- **Fast, reliable speech recognition** — tuned pause/energy thresholds, one-time
  mic calibration, longer listening windows. Optional offline Faster-Whisper
  backend for accuracy without needing internet.
- **Groq as the brain** — any command Jarvis doesn't recognize locally is
  answered by Groq, with a professional system prompt and short-term
  conversation memory for natural follow-ups.
- **Bilingual command handling** — common English, Urdu, and mixed Roman Urdu
  phrases are normalized through the same command router.
- **Windows automation** — open/close apps, shutdown/restart/sleep/lock,
  volume, brightness, CPU/RAM/battery/storage, Wi-Fi status, IP address,
  running processes, Control Panel, Settings, Task Manager, Device Manager,
  Registry Editor, Services, CMD, PowerShell, Windows Terminal, screenshots,
  screen recording, and clipboard actions.
- **Smart file search & management** — create/rename/move/copy/delete files
  and folders, fuzzy-search Desktop/Downloads/Documents/Pictures/Home, open
  the latest matching file, and handle duplicates more gracefully.
- **Media control** — "play <song/movie>" searches your local Music/Videos
  folders first, then automatically falls back to YouTube if nothing local is
  found. Play/pause/next/previous and Spotify shortcuts included.
- **Coding assistant** — "generate a Flask login system" writes real code
  and can save it straight into the `generated_code/` folder without
  regenerating the file.
- **Browser automation** — search Google/YouTube/GitHub/Stack Overflow, open
  Gmail/LinkedIn/ChatGPT/Groq/Groq Console/Docs/Drive directly.
- **Safety confirmations** — delete / shutdown / restart always ask "are you
  sure?" before doing anything.
- **Notes, reminders, jokes, and motivational quotes** carried over from the
  original project.
- **Clean error handling** — Jarvis never crashes or shows a raw traceback;
  it explains briefly and keeps going.
- **Theme toggle** — the Streamlit UI supports persisted dark and light modes.

## Project Structure

```text
Jarvis/
├── jarvis.py                 # Terminal, wake-word driven engine
├── app.py                    # Streamlit browser UI
├── config.py                 # All settings in one place (.env driven)
├── requirements.txt
├── README.md
├── .env.example
├── core/
│   ├── speech.py              # Microphone input, wake word, continuous listening
│   ├── speak.py                # Text-to-speech (one reused engine instance)
│   ├── ai.py                   # Groq brain: system prompt + memory
│   └── command_handler.py      # Routes every command to the right module
├── commands/
│   ├── system_control.py       # Apps, power, volume, brightness, system info
│   ├── files.py                 # File/folder create, rename, move, delete, search
│   ├── media.py                  # Local media playback + YouTube fallback
│   ├── coder.py                   # AI-powered code generation + saving
│   ├── browser.py                  # Google/YouTube/GitHub/Stack Overflow search
│   ├── notes.py
│   ├── reminders.py
│   └── fun.py
├── generated_code/            # Where Jarvis saves code you ask it to write
└── data/
    ├── notes.txt
    └── reminders.json
```

## Requirements

- Python 3.12+
- Windows 11 (system automation commands are Windows-specific)
- A working microphone
- A Groq API key from [Groq Console](https://console.groq.com/keys)

## Installation

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Setup

1. Copy `.env.example` to `.env`.
2. Put your Groq API key into `.env`.

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
```

## Run

Terminal (hands-free, wake word):

```powershell
python jarvis.py
```

Browser UI:

```powershell
streamlit run app.py
```

## Example commands

- "Hey Jarvis" → "Who is Elon Musk?"
- "Create a folder called AI on Desktop"
- "Generate a Flask login system" → then "save that code"
- "Open VS Code"
- "Play Interstellar" (checks local files first, then YouTube)
- "Find my resume"
- "Open latest screenshot"
- "Copy this text to clipboard"
- "Start screen recording"
- "Set a reminder to submit the assignment"
- "What's my CPU usage?"
- "Shut down the computer" → Jarvis asks you to confirm first

## Notes

- If the microphone doesn't work, check Windows microphone permissions.
- If PyAudio installation fails, install the Windows build tools, or use a
  prebuilt wheel matching your Python version.
- Unknown commands are always sent to Groq automatically.
- Optional but recommended: set `USE_FASTER_WHISPER=true` in `.env` and
  `pip install faster-whisper` for offline, multilingual speech recognition.
- Optional: `pip install screen-brightness-control` to enable "set brightness".

## Error Handling & Safety

- Microphone failures, speech recognition issues, missing API keys, and
  file/JSON problems are all handled with friendly messages, never crashes.
- Deleting files/folders and shutting down/restarting the PC always ask for
  a spoken "yes" before doing anything.
