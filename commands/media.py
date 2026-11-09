"""Media playback commands for Jarvis.

Searches the user's local Music/Videos folders first; if nothing is found
locally it automatically falls back to searching YouTube, so "play
Interstellar" always does something useful.
"""

from __future__ import annotations

import os
import webbrowser
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote_plus

import pyautogui

from config import Config


class MediaCommands:
    """Play, pause, and skip media, locally or on YouTube."""

    def __init__(self) -> None:
        self.config = Config()

    @staticmethod
    def _score_match(query: str, candidate: str) -> float:
        query_lower = query.lower().strip()
        candidate_lower = candidate.lower().strip()
        if not query_lower:
            return 0.0
        score = SequenceMatcher(None, query_lower, candidate_lower).ratio()
        if query_lower in candidate_lower:
            score += 0.5
        return score

    def play(self, query: str) -> str:
        keyword = query.lower().strip()
        if not keyword:
            return "What would you like me to play?"

        candidates = []
        for folder_key in ("music", "videos"):
            folder = self.config.known_locations.get(folder_key)
            if not folder or not folder.exists():
                continue
            for path in folder.rglob("*"):
                if path.is_file():
                    score = self._score_match(keyword, path.name)
                    if score > 0:
                        candidates.append((score, path.stat().st_mtime, path))

        if candidates:
            _, _, best_match = max(candidates, key=lambda item: (item[0], item[1]))
            try:
                os.startfile(str(best_match))
                return f"Playing '{best_match.name}' locally."
            except Exception as exc:
                return f"I found '{best_match.name}' but couldn't play it: {exc}"

        # Nothing found locally -- fall back to YouTube automatically.
        from commands.browser import BrowserCommands

        result = BrowserCommands().open_youtube_first_result(query)
        if result.startswith("Playing "):
            return result
        return f"I couldn't find '{query}' locally, so I opened it on YouTube."

    def pause_or_resume(self) -> str:
        pyautogui.press("playpause")
        return "Toggled play/pause."

    def next_track(self) -> str:
        pyautogui.press("nexttrack")
        return "Skipped to the next track."

    def previous_track(self) -> str:
        pyautogui.press("prevtrack")
        return "Went back to the previous track."

    def open_spotify(self) -> str:
        try:
            os.system("start spotify")
            return "Opening Spotify."
        except Exception as exc:
            return f"I couldn't open Spotify: {exc}"
