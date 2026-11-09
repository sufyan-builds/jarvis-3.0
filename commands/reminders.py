"""Reminder storage commands for Jarvis.

This module stores reminder items in a JSON file and reads them back.
"""

from __future__ import annotations

import json
from pathlib import Path


class ReminderCommands:
    """Manage reminders as JSON records."""

    def __init__(self) -> None:
        self.reminders_path = Path(__file__).resolve().parents[1] / "data" / "reminders.json"
        self.reminders_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.reminders_path.exists():
            self.reminders_path.write_text("[]", encoding="utf-8")

    def save_reminder(self, reminder_text: str) -> None:
        """Append a new reminder to the JSON file."""
        with self.reminders_path.open("r", encoding="utf-8") as file:
            reminders = json.load(file)

        reminders.append(reminder_text)

        with self.reminders_path.open("w", encoding="utf-8") as file:
            json.dump(reminders, file, indent=4)

    def read_reminders(self) -> str:
        """Read and return all saved reminders."""
        with self.reminders_path.open("r", encoding="utf-8") as file:
            reminders = json.load(file)

        if not reminders:
            return "No reminders have been saved yet."

        return "\n".join([f"- {item}" for item in reminders])
