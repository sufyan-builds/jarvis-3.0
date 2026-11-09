"""Coding assistant commands for Jarvis.

Turns Jarvis into a lightweight programming assistant: it asks the AI brain for
code and can save the result straight to a file inside generated_code/, so
requests like "generate a Flask login system" produce a real file the user
can open, instead of just spoken text.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

from config import Config
from core.ai import GroqAssistant

# Reasonable default file extensions for common languages Jarvis is asked
# to generate code in. Falls back to .txt for anything unrecognized.
EXTENSIONS = {
    "python": ".py",
    "c++": ".cpp",
    "cpp": ".cpp",
    "java": ".java",
    "sql": ".sql",
    "html": ".html",
    "css": ".css",
    "javascript": ".js",
    "react": ".jsx",
    "streamlit": ".py",
    "flask": ".py",
}


class CoderAssistant:
    """Generates code with the AI backend and optionally saves it to disk."""

    def __init__(self, ai: GroqAssistant) -> None:
        self.ai = ai
        self.config = Config()
        self._last_task: str = ""
        self._last_language: str = ""
        self._last_code: str = ""

    def _safe_filename(self, task: str, filename: str = "") -> str:
        safe_name = filename or "_".join(task.lower().split())[:40]
        return safe_name.replace("/", "_").replace("\\", "_")

    def _unique_path(self, base_name: str, ext: str) -> Path:
        candidate = self.config.generated_code_dir / f"{base_name}{ext}"
        if not candidate.exists():
            return candidate

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidate = self.config.generated_code_dir / f"{base_name}_{timestamp}{ext}"
        counter = 1
        while candidate.exists():
            candidate = self.config.generated_code_dir / f"{base_name}_{timestamp}_{counter}{ext}"
            counter += 1
        return candidate

    def generate(self, task: str, language: str = "") -> str:
        """Generate code for a task and return a short spoken summary (code is printed, not spoken)."""
        if not self.ai.is_available:
            return "The AI service isn't available, so I can't generate code right now."

        code = self.ai.generate_code(task, language)
        if not code:
            return "I wasn't able to generate that code."

        self._last_task = task
        self._last_language = language
        self._last_code = code

        print("\n" + "=" * 60)
        print(f"Generated code for: {task}")
        print("=" * 60)
        print(code)
        print("=" * 60 + "\n")

        return f"I've generated the {language or 'code'} for '{task}'. You can see it in the console. Say 'save that code' if you'd like it saved to a file."

    def save_last(self, task: str, language: str, filename: str = "") -> str:
        """Save the last generated code, or generate fresh code if nothing is cached."""
        if not self.ai.is_available:
            return "The AI service isn't available, so I can't generate code right now."

        code = self._last_code
        if not code or self._last_task != task:
            code = self.ai.generate_code(task, language)
            if not code:
                return "I wasn't able to generate that code to save."
            self._last_task = task
            self._last_language = language
            self._last_code = code

        if not code:
            return "I wasn't able to generate that code to save."

        self.config.generated_code_dir.mkdir(parents=True, exist_ok=True)
        ext = EXTENSIONS.get(language.lower(), ".txt")
        safe_name = self._safe_filename(task, filename)
        file_path = self._unique_path(safe_name, ext)

        if not code:
            return "I wasn't able to generate that code to save."

        try:
            file_path.write_text(code, encoding="utf-8")
            return f"Saved the generated code to {file_path.name} in the generated_code folder."
        except Exception as exc:
            return f"I generated the code but couldn't save it: {exc}"

    def save_cached(self, filename: str = "") -> str:
        """Save the most recent generated code without asking the model again."""
        if not self._last_code:
            return "I don't have any recently generated code to save yet."
        return self.save_last(self._last_task, self._last_language, filename)
