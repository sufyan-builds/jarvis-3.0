"""File and folder commands for Jarvis.

Handles creating, renaming, moving, and deleting files/folders, plus "smart"
searching across common locations (Desktop, Downloads, Documents, ...) so the
user can say things like "find my resume" without giving an exact path.

Destructive actions (delete, move) do not ask for confirmation themselves --
core/command_handler.py is responsible for confirming with the user before
calling delete_folder / delete_file / move_item. This keeps the "are you
sure?" logic in one place instead of scattered across every command module.
"""

from __future__ import annotations

import shutil
import os
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

from config import Config


class FileCommands:
    """Create, organize, and search files/folders in known locations."""

    def __init__(self) -> None:
        self.config = Config()

    def _resolve_location(self, location: Optional[str]) -> Path:
        """Turn a spoken location name ("desktop", "downloads", ...) into a real path."""
        if not location:
            return self.config.known_locations["desktop"]
        key = location.strip().lower()
        return self.config.known_locations.get(key, self.config.known_locations["desktop"])

    def _search_roots(self):
        return [
            self.config.known_locations["desktop"],
            self.config.known_locations["downloads"],
            self.config.known_locations["documents"],
            self.config.known_locations["pictures"],
            self.config.known_locations["home"],
        ]

    @staticmethod
    def _score_match(keyword: str, candidate_name: str) -> float:
        keyword_lower = keyword.lower().strip()
        candidate_lower = candidate_name.lower().strip()
        if not keyword_lower:
            return 0.0

        score = SequenceMatcher(None, keyword_lower, candidate_lower).ratio()
        if keyword_lower in candidate_lower:
            score += 0.5
        if keyword_lower in Path(candidate_lower).stem:
            score += 0.2
        return score

    def _ranked_matches(self, keyword: str, max_results: int = 5):
        candidates = []
        for root in self._search_roots():
            if not root.exists():
                continue
            try:
                for path in root.rglob("*"):
                    if path.is_file():
                        score = self._score_match(keyword, path.name)
                        if score > 0:
                            candidates.append((score, path.stat().st_mtime, path))
            except (PermissionError, OSError):
                continue

        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [path for _, _, path in candidates[:max_results]]

    # ---------- Create ----------

    def create_folder(self, name: str, location: Optional[str] = None) -> str:
        base = self._resolve_location(location)
        target = base / name
        try:
            target.mkdir(parents=True, exist_ok=True)
            return f"Created folder '{name}' in {base.name}."
        except Exception as exc:
            return f"I couldn't create that folder: {exc}"

    def create_file(self, name: str, location: Optional[str] = None) -> str:
        base = self._resolve_location(location)
        target = base / name
        try:
            base.mkdir(parents=True, exist_ok=True)
            target.touch(exist_ok=True)
            return f"Created file '{name}' in {base.name}."
        except Exception as exc:
            return f"I couldn't create that file: {exc}"

    def open_folder(self, name: str = "", location: Optional[str] = None) -> str:
        base = self._resolve_location(location)
        target = base / name if name else base
        if not target.exists() or not target.is_dir():
            return f"I couldn't find folder '{name or base.name}'."
        try:
            os.startfile(str(target))
            return f"Opening folder '{target.name}'."
        except Exception as exc:
            return f"I couldn't open that folder: {exc}"

    def open_file(self, name: str, location: Optional[str] = None) -> str:
        base = self._resolve_location(location)
        target = base / name
        if not target.exists() or not target.is_file():
            return f"I couldn't find file '{name}' in {base.name}."
        try:
            os.startfile(str(target))
            return f"Opening file '{target.name}'."
        except Exception as exc:
            return f"I couldn't open that file: {exc}"

    # ---------- Rename / Move / Copy ----------

    def rename_item(self, old_name: str, new_name: str, location: Optional[str] = None) -> str:
        base = self._resolve_location(location)
        source = base / old_name
        if not source.exists():
            return f"I couldn't find '{old_name}' in {base.name}."
        try:
            source.rename(base / new_name)
            return f"Renamed '{old_name}' to '{new_name}'."
        except Exception as exc:
            return f"I couldn't rename that: {exc}"

    def move_item(self, name: str, source_location: Optional[str], dest_location: Optional[str]) -> str:
        source_base = self._resolve_location(source_location)
        dest_base = self._resolve_location(dest_location)
        source = source_base / name
        if not source.exists():
            return f"I couldn't find '{name}' in {source_base.name}."
        try:
            dest_base.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest_base / name))
            return f"Moved '{name}' to {dest_base.name}."
        except Exception as exc:
            return f"I couldn't move that: {exc}"

    def copy_item(self, name: str, source_location: Optional[str], dest_location: Optional[str]) -> str:
        source_base = self._resolve_location(source_location)
        dest_base = self._resolve_location(dest_location)
        source = source_base / name
        if not source.exists():
            return f"I couldn't find '{name}' in {source_base.name}."
        try:
            dest_base.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(str(source), str(dest_base / name), dirs_exist_ok=True)
            else:
                shutil.copy2(str(source), str(dest_base / name))
            return f"Copied '{name}' to {dest_base.name}."
        except Exception as exc:
            return f"I couldn't copy that: {exc}"

    # ---------- Delete (destructive -- caller must confirm first) ----------

    def delete_folder(self, name: str, location: Optional[str] = None) -> str:
        base = self._resolve_location(location)
        target = base / name
        if not target.exists():
            return f"I couldn't find folder '{name}' in {base.name}."
        try:
            shutil.rmtree(target)
            return f"Deleted folder '{name}'."
        except Exception as exc:
            return f"I couldn't delete that folder: {exc}"

    def delete_file(self, name: str, location: Optional[str] = None) -> str:
        base = self._resolve_location(location)
        target = base / name
        if not target.exists():
            return f"I couldn't find file '{name}' in {base.name}."
        try:
            target.unlink()
            return f"Deleted file '{name}'."
        except Exception as exc:
            return f"I couldn't delete that file: {exc}"

    # ---------- Smart search ----------

    def search(self, keyword: str, max_results: int = 5) -> str:
        """Search common user folders with fuzzy filename matching."""
        matches = self._ranked_matches(keyword, max_results=max_results)

        if not matches:
            return f"I couldn't find anything matching '{keyword}' in Desktop, Downloads, or Documents."

        listing = "; ".join(f"{p.name} ({p.parent.name})" for p in matches)
        return f"Found {len(matches)} match(es): {listing}."

    def open_match(self, keyword: str) -> str:
        """Search for a file and open the best-ranked match."""
        candidates = self._ranked_matches(keyword, max_results=10)

        if not candidates:
            return f"I couldn't find anything matching '{keyword}'."

        newest = max(candidates, key=lambda p: (self._score_match(keyword, p.name), p.stat().st_mtime))
        try:
            import os
            os.startfile(str(newest))  # Windows-only, matches this project's target OS
            return f"Opening {newest.name}."
        except Exception as exc:
            return f"I found {newest.name} but couldn't open it: {exc}"

    def find_latest(self, keyword: str = "") -> str:
        """Find the most recently modified file matching an optional keyword."""
        candidates = []
        for root in (
            self.config.known_locations["desktop"],
            self.config.known_locations["downloads"],
            self.config.known_locations["pictures"],
            self.config.known_locations["documents"],
        ):
            if root.exists():
                try:
                    for path in root.rglob("*"):
                        if path.is_file() and (not keyword or self._score_match(keyword, path.name) > 0):
                            candidates.append(path)
                except (PermissionError, OSError):
                    continue

        if not candidates:
            return f"I couldn't find any recent files matching '{keyword}'." if keyword else "I couldn't find any recent files."

        newest = max(candidates, key=lambda p: (p.stat().st_mtime, self._score_match(keyword, p.name)))
        try:
            import os
            os.startfile(str(newest))
            return f"Opening the latest match: {newest.name}."
        except Exception as exc:
            return f"Found {newest.name} but couldn't open it: {exc}"
