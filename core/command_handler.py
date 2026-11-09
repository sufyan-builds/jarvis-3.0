"""Command routing logic for Jarvis.

This is the single "brain" that both the Streamlit UI (app.py) and the
terminal engine (jarvis.py) call into, so command logic only has to be
written once and both interfaces behave identically.

Flow for every command:
  1. If Jarvis is waiting for a yes/no confirmation, handle that first.
  2. Check for an exit phrase.
  3. Try to match a known local command (fast, free, works offline).
    4. If nothing matches, ask the AI brain to answer naturally.

Destructive actions (delete, shutdown, restart, ...) never run immediately --
handle_command() stores the action and asks the user to confirm first.

A note on casing: matching is always done on a lowercased copy of the text,
but names extracted from the command (folder names, note text, search
keywords, ...) are pulled from the ORIGINAL text so "Projects" stays
"Projects" instead of becoming "projects".
"""

from __future__ import annotations

import re
from typing import Callable, Optional

from commands.browser import BrowserCommands
from commands.coder import CoderAssistant
from commands.files import FileCommands
from commands.fun import FunCommands
from commands.media import MediaCommands
from commands.notes import NotesCommands
from commands.reminders import ReminderCommands
from commands.system_control import SystemController
from config import Config
from core.ai import GroqAssistant
from core.language import normalize_command_text
from core.speak import TextToSpeech

EXIT_KEYWORDS = {"exit", "quit", "close jarvis", "goodbye", "bye", "power off", "shut down jarvis"}
LOCATION_SUFFIXES = ("on desktop", "in desktop", "on downloads", "in downloads",
                      "on documents", "in documents", "to desktop", "to downloads", "to documents")


class CommandHandler:
    """Central router for all voice/text commands."""

    def __init__(self, tts: TextToSpeech, ai: GroqAssistant) -> None:
        self.tts = tts
        self.ai = ai
        self.config = Config()

        self.system = SystemController()
        self.browser = BrowserCommands()
        self.files = FileCommands()
        self.media = MediaCommands()
        self.notes = NotesCommands()
        self.reminders = ReminderCommands()
        self.fun = FunCommands()
        self.coder = CoderAssistant(ai)

        # Holds a pending destructive action while we wait for confirmation.
        self._pending_action: Optional[Callable[[], str]] = None
        self._pending_description: str = ""

    # ---------- normalization ----------

    def normalize(self, text: str) -> str:
        """Return a normalized copy of text for keyword matching."""
        return normalize_command_text(text)

    def should_exit(self, command: str) -> bool:
        return any(keyword in command for keyword in EXIT_KEYWORDS)

    def _extract_after(self, command: str, raw: str, *phrases: str) -> str:
        """Return whatever comes after the first matching phrase, with original casing."""
        for phrase in phrases:
            idx = command.find(phrase)
            if idx != -1:
                result = raw[idx + len(phrase):].strip()
                return self._strip_location_suffix(result)
        return ""

    def _extract_browser_query(self, raw: str, site: str) -> str:
        query = raw
        query = re.sub(r"\b(search|find|search for|look for|dhoondo|dhundo|talash karo|talash)\b", " ", query, flags=re.IGNORECASE)
        query = re.sub(rf"\b({re.escape(site)})\b", " ", query, flags=re.IGNORECASE)
        query = re.sub(r"\b(for|on|par|pe|mein|me|ko|karo|please)\b", " ", query, flags=re.IGNORECASE)
        query = re.sub(r"\s+", " ", query).strip(" -,:;")
        return query

    def _strip_location_suffix(self, text: str) -> str:
        lowered = text.lower()
        for suffix in LOCATION_SUFFIXES:
            if lowered.endswith(suffix):
                text = text[: -len(suffix)].strip()
                break
        for word in ("called ", "named "):
            if text.lower().startswith(word):
                text = text[len(word):].strip()
        return text

    def _is_destructive(self, command: str) -> bool:
        return any(word in command for word in self.config.destructive_keywords)

    def _ask_confirmation(self, description: str, action: Callable[[], str]) -> str:
        self._pending_action = action
        self._pending_description = description
        return f"Are you sure you want to {description}? Say yes to confirm or no to cancel."

    # ---------- main entry point ----------

    def handle_command(self, text: str) -> Optional[str]:
        """Choose the correct action and return a spoken response, or None to exit."""
        raw = text.strip()
        command = self.normalize(raw)

        # 1. Resolve any pending confirmation first.
        if self._pending_action is not None:
            if any(word in command for word in self.config.confirm_words):
                action = self._pending_action
                self._pending_action = None
                self._pending_description = ""
                return action()
            if any(word in command for word in self.config.cancel_words):
                self._pending_action = None
                self._pending_description = ""
                return "Okay, cancelled."
            return f"Please say yes or no. Do you want to {self._pending_description}?"

        # 2. Exit phrase.
        if self.should_exit(command):
            return None

        # 3. Local, fast, deterministic commands.
        response = self._route_local_command(command, raw)
        if response is not None:
            return response

        # 4. Fall back to the AI brain for anything Jarvis doesn't recognize.
        return self.ai.ask(raw)

    # ---------- local command routing ----------

    def _route_local_command(self, command: str, raw: str) -> Optional[str]:
        handlers = (
            self._handle_apps,
            self._handle_websites,
            self._handle_browser_search,
            self._handle_power,
            self._handle_windows_tools,
            self._handle_clipboard,
            self._handle_volume_and_brightness,
            self._handle_system_info,
            self._handle_files,
            self._handle_media,
            self._handle_notes,
            self._handle_reminders,
            self._handle_coding,
            self._handle_fun,
        )
        for handler in handlers:
            result = handler(command, raw)
            if result is not None:
                return result
        return None

    def _handle_apps(self, command: str, raw: str) -> Optional[str]:
        open_triggers = ("open ", "launch ", "start ")
        close_triggers = ("close ", "quit ", "kill ")

        for app_name in ("chrome", "edge", "vscode", "vs code", "visual studio code", "notepad",
                          "calculator", "paint", "terminal", "powershell", "cmd", "explorer",
                          "file explorer", "spotify"):
            if any(f"{trigger}{app_name}" in command or f"{app_name} {trigger.strip()}" in command for trigger in open_triggers):
                key = "vscode" if "code" in app_name else app_name
                return self.system.open_app(key)
            if any(f"{trigger}{app_name}" in command or f"{app_name} {trigger.strip()}" in command for trigger in close_triggers):
                key = "vscode" if "code" in app_name else app_name
                return self.system.close_app(key)
        return None

    def _handle_websites(self, command: str, raw: str) -> Optional[str]:
        for site in ("google", "youtube", "github", "stackoverflow", "linkedin", "gmail", "chatgpt", "grok", "groq", "docs", "drive"):
            if f"open {site}" in command or f"launch {site}" in command or (site in command and any(term in command for term in ("open", "launch", "start"))):
                return self.system.open_website(site)
        return None

    def _handle_browser_search(self, command: str, raw: str) -> Optional[str]:
        if "google" in command and "search" in command:
            query = self._extract_after(command, raw, "search google for", "search google", "google search for", "google search") or self._extract_browser_query(raw, "google")
            return self.browser.search_google(query) if query else "What would you like me to search for on Google?"
        if "youtube" in command and "search" in command:
            query = self._extract_after(command, raw, "search youtube for", "search youtube", "youtube search for", "youtube search") or self._extract_browser_query(raw, "youtube")
            return self.browser.search_youtube(query) if query else "What would you like me to search for on YouTube?"
        if "github" in command and "search" in command:
            query = self._extract_after(command, raw, "search github for", "search github") or self._extract_browser_query(raw, "github")
            return self.browser.search_github(query) if query else "What should I search for on GitHub?"
        if "stackoverflow" in command and "search" in command or "stack overflow" in command and "search" in command:
            query = self._extract_after(command, raw, "search stack overflow for", "search stack overflow",
                                         "search stackoverflow for", "search stackoverflow") or self._extract_browser_query(raw, "stackoverflow")
            return self.browser.search_stackoverflow(query) if query else "What should I search for on Stack Overflow?"
        return None

    def _handle_power(self, command: str, raw: str) -> Optional[str]:
        if "shutdown" in command or "shut down" in command:
            return self._ask_confirmation("shut down the computer", self.system.shutdown)
        if "restart" in command or "reboot" in command:
            return self._ask_confirmation("restart the computer", self.system.restart)
        if "sleep" in command and "system" not in command:
            return self.system.sleep()
        if "lock" in command and ("pc" in command or "computer" in command or "screen" in command):
            return self.system.lock()
        return None

    def _handle_windows_tools(self, command: str, raw: str) -> Optional[str]:
        if "control panel" in command:
            return self.system.open_control_panel()
        if "settings" in command:
            return self.system.open_settings()
        if "task manager" in command:
            return self.system.open_task_manager()
        if "device manager" in command:
            return self.system.open_device_manager()
        if "registry editor" in command or "regedit" in command:
            return self._ask_confirmation("open the Registry Editor", self.system.open_registry_editor)
        if "services" in command and "open" in command:
            return self.system.open_services()
        if command == "cmd" or "open cmd" in command or "command prompt" in command:
            return self.system.open_cmd()
        if "powershell" in command:
            return self.system.open_powershell()
        if "windows terminal" in command or command == "terminal" or "open terminal" in command:
            return self.system.open_terminal()
        if "switch window" in command or "switch windows" in command or "alt tab" in command:
            return self.system.switch_window()
        if "show desktop" in command or "desktop" in command and "show" in command:
            return self.system.show_desktop()
        if "task view" in command or "view tasks" in command:
            return self.system.open_task_view()
        if "screenshot" in command or "screen shot" in command:
            return self.system.screenshot()
        if "record screen" in command or "screen record" in command or "start recording" in command or "start screen recording" in command:
            return self.system.start_screen_recording()
        if "stop recording" in command or "stop screen recording" in command:
            return self.system.stop_screen_recording()
        if "empty recycle bin" in command or "empty bin" in command or "empty trash" in command:
            return self._ask_confirmation("empty the Recycle Bin", self.system.empty_recycle_bin)
        return None

    def _handle_clipboard(self, command: str, raw: str) -> Optional[str]:
        if any(term in command for term in ("copy to clipboard", "copy text", "copy this", "copy that", "clipboard copy")):
            text = self._extract_after(command, raw, "copy to clipboard", "copy text", "copy this", "copy that")
            if not text:
                return "What text should I copy to the clipboard?"
            return self.system.copy_to_clipboard(text)
        if "paste clipboard" in command or "paste from clipboard" in command or "what is on the clipboard" in command:
            clipboard_text = self.system.read_clipboard()
            return f"Clipboard says: {clipboard_text}" if clipboard_text and clipboard_text != "The clipboard is empty." else clipboard_text
        if "clear clipboard" in command or "empty clipboard" in command:
            return self.system.clear_clipboard()
        return None

    def _handle_volume_and_brightness(self, command: str, raw: str) -> Optional[str]:
        if "volume up" in command:
            return self.system.volume_up()
        if "volume down" in command:
            return self.system.volume_down()
        if "mute" in command:
            return self.system.mute()
        if "brightness" in command:
            digits = "".join(ch for ch in command if ch.isdigit())
            if digits:
                return self.system.set_brightness(int(digits))
            return "What percent would you like the brightness set to?"
        return None

    def _handle_system_info(self, command: str, raw: str) -> Optional[str]:
        if "what time" in command or "tell me the time" in command or command.strip() == "time":
            return f"The current time is {self.system.current_time()}."
        if "what date" in command or "today's date" in command or "tell me the date" in command:
            return self.system.current_date()
        if "cpu" in command:
            return f"Current CPU usage is {self.system.cpu_usage()} percent."
        if "ram" in command or "memory usage" in command:
            return f"Current RAM usage is {self.system.ram_usage()} percent."
        if "storage" in command or "disk space" in command:
            return self.system.storage_usage()
        if "battery" in command:
            percent = self.system.battery_percentage()
            return f"Battery is at {percent} percent." if percent is not None else "I couldn't read battery information (this may be a desktop PC)."
        if "ip address" in command:
            return self.system.ip_address()
        if "wifi" in command or "wi-fi" in command:
            return self.system.wifi_status()
        if "running processes" in command or "what's running" in command or "whats running" in command:
            return self.system.running_processes()
        return None

    def _handle_files(self, command: str, raw: str) -> Optional[str]:
        location = self._detect_location(command)

        if any(p in command for p in ("open folder", "folder open", "open the folder", "open my folder", "open downloads", "downloads open", "open desktop", "desktop open", "open documents", "documents open", "open pictures", "pictures open", "open music", "music open", "open videos", "videos open")):
            folder_name = self._extract_after(command, raw, "open folder called", "open folder named", "open folder", "open the folder called", "open the folder")
            return self.files.open_folder(folder_name, location)

        if any(p in command for p in ("open file", "file open", "open the file", "open my file")):
            file_name = self._extract_after(command, raw, "open file called", "open file named", "open file", "open the file called", "open the file")
            return self.files.open_file(file_name, location) if file_name else "Which file should I open?"

        if "create folder" in command or "folder create" in command or "make folder" in command or "new folder" in command:
            name = self._extract_after(command, raw, "create folder called", "create folder named", "create folder",
                                        "make folder called", "make folder", "new folder called", "new folder")
            return self.files.create_folder(name, location) if name else "What should I name the folder?"

        if "create file" in command or "file create" in command or "make file" in command or "new file" in command:
            name = self._extract_after(command, raw, "create file called", "create file named", "create file",
                                        "make file called", "make file", "new file called", "new file")
            return self.files.create_file(name, location) if name else "What should I name the file?"

        if "delete folder" in command or "remove folder" in command:
            name = self._extract_after(command, raw, "delete folder", "remove folder")
            if not name:
                return "Which folder should I delete?"
            return self._ask_confirmation(f"delete the folder '{name}'", lambda n=name: self.files.delete_folder(n, location))

        if "delete file" in command or "remove file" in command:
            name = self._extract_after(command, raw, "delete file", "remove file")
            if not name:
                return "Which file should I delete?"
            return self._ask_confirmation(f"delete the file '{name}'", lambda n=name: self.files.delete_file(n, location))

        if "rename " in command:
            # "rename OldName to NewName [on desktop]"
            body_command = command.split("rename ", 1)[1]
            idx = command.find("rename ")
            body_raw = raw[idx + len("rename "):]
            if " to " in body_command:
                split_at = body_command.find(" to ")
                old_name = body_raw[:split_at].strip()
                new_name = self._strip_location_suffix(body_raw[split_at + 4:].strip())
                return self.files.rename_item(old_name, new_name, location)
            return "Please tell me the current name and the new name, like 'rename notes.txt to notes-old.txt'."

        if "find" in command or "search" in command or "search for" in command or "search my computer" in command:
            keyword = self._extract_after(command, raw, "find my", "find", "search for", "search my computer for",
                                          "dhoondo", "dhundo", "talash karo", "talash")
            return self.files.search(keyword) if keyword else None

        if "open latest" in command or "open my latest" in command:
            keyword = self._extract_after(command, raw, "open latest", "open my latest")
            return self.files.find_latest(keyword)

        return None

    def _handle_media(self, command: str, raw: str) -> Optional[str]:
        if command.startswith("play ") or command.endswith(" play") or " play " in command or "play" in command:
            query = self._extract_after(command, raw, "play", "chalao", "chala do", "chala")
            return self.media.play(query) if query else "What would you like me to play?"
        if "pause" in command or "resume" in command:
            return self.media.pause_or_resume()
        if "next song" in command or "next track" in command:
            return self.media.next_track()
        if "previous song" in command or "previous track" in command:
            return self.media.previous_track()
        if "open spotify" in command:
            return self.media.open_spotify()
        return None

    def _handle_notes(self, command: str, raw: str) -> Optional[str]:
        if any(p in command for p in ("save note", "note save", "write note", "note write", "remember this", "save this note")):
            note_text = self._extract_after(command, raw, "save note", "write note", "remember this", "save this note",
                                            "note save", "note write")
            if not note_text:
                return "Please tell me the note text to save."
            self.notes.save_note(note_text)
            return "Note saved successfully."
        if "read notes" in command or "read note" in command:
            return self.notes.read_notes()
        return None

    def _handle_reminders(self, command: str, raw: str) -> Optional[str]:
        if any(p in command for p in ("save reminder", "reminder save", "set reminder", "remind me")):
            reminder_text = self._extract_after(command, raw, "save reminder", "set reminder", "remind me",
                                                "reminder save")
            if not reminder_text:
                return "Please tell me the reminder text to save."
            self.reminders.save_reminder(reminder_text)
            return "Reminder saved successfully."
        if "read reminders" in command or "read reminder" in command:
            return self.reminders.read_reminders()
        return None

    def _handle_coding(self, command: str, raw: str) -> Optional[str]:
        if "save that code" in command or "save the code" in command:
            return self.coder.save_cached()

        generate_triggers = ("generate ", "write ", "create a ", "build a ")
        code_words = ("code", "script", "function", "class", "app", "flask", "streamlit", "sql", "html", "css",
                      "react", "program", "project")
        if any(command.startswith(t) for t in generate_triggers) and any(w in command for w in code_words):
            language = self._detect_language(command)
            return self.coder.generate(raw, language)

        return None

    def _handle_fun(self, command: str, raw: str) -> Optional[str]:
        if "joke" in command:
            return self.fun.tell_joke()
        if "quote" in command or "motivation" in command:
            return self.fun.motivational_quote()
        return None

    # ---------- small entity-extraction helpers ----------

    def _detect_location(self, command: str) -> Optional[str]:
        for key in self.config.known_locations:
            if key in command:
                return key
        return None

    def _detect_language(self, text: str) -> str:
        lowered = text.lower()
        languages = ["python", "c++", "java", "sql", "html", "css", "javascript", "react", "streamlit", "flask"]
        for lang in languages:
            if lang in lowered:
                return lang
        return "python"
