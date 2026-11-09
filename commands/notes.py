"""Notes storage commands for Jarvis.

This module saves notes into a text file and reads them back on request.
"""

from __future__ import annotations

from pathlib import Path


class NotesCommands:
    """Simple notes file manager."""

    def __init__(self) -> None:
        self.notes_path = Path(__file__).resolve().parents[1] / "data" / "notes.txt"

    def save_note(self, note_text: str) -> None:
        """Append a note to the notes text file."""
        self.notes_path.parent.mkdir(parents=True, exist_ok=True)
        with self.notes_path.open("a", encoding="utf-8") as file:
            file.write(note_text + "\n")

    def read_notes(self) -> str:
        """Read all saved notes or return a helpful message if there are none."""
        if not self.notes_path.exists():
            return "No notes have been saved yet."

        with self.notes_path.open("r", encoding="utf-8") as file:
            notes = file.read().strip()

        if not notes:
            return "No notes have been saved yet."
        return notes
