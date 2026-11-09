"""Configuration values for the Jarvis project.

This file loads sensitive values from environment variables using dotenv.
It keeps the project beginner-friendly and easy to customize: every setting
Jarvis needs lives in one place.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Simple configuration holder class.

    It reads environment variables and exposes them through easy-to-use
    attributes so the rest of the project never has to call os.getenv directly.
    """

    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parent
        load_dotenv(project_root / ".env")

        # --- AI ---
        self.ai_provider = os.getenv("AI_PROVIDER", "groq").strip().lower()
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        # Keep the model configurable so switching models later only requires
        # an environment update.
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        self.ai_temperature = float(os.getenv("AI_TEMPERATURE", "0.4"))
        self.max_memory_turns = int(os.getenv("MAX_MEMORY_TURNS", "6"))

        # --- Wake word / listening ---
        self.wake_words = [
            w.strip().lower()
            for w in os.getenv("WAKE_WORDS", "hey jarvis,jarvis").split(",")
            if w.strip()
        ]
        self.use_faster_whisper = os.getenv("USE_FASTER_WHISPER", "true").lower() == "true"
        self.whisper_model_size = os.getenv("WHISPER_MODEL_SIZE", "base.en")
        # How long Jarvis stays awake with no command heard before going back to sleep.
        self.sleep_after_seconds = int(os.getenv("SLEEP_AFTER_SECONDS", "300"))

        # --- Web shortcuts ---
        self.google_search_url = "https://www.google.com/search?q="
        self.youtube_url = "https://www.youtube.com/results?search_query="

        # --- Filesystem locations Jarvis is allowed to search/act in ---
        home = Path.home()
        self.known_locations = {
            "desktop": home / "Desktop",
            "downloads": home / "Downloads",
            "documents": home / "Documents",
            "pictures": home / "Pictures",
            "music": home / "Music",
            "videos": home / "Videos",
            "home": home,
        }

        # --- Generated code output folder ---
        self.generated_code_dir = project_root / "generated_code"

        # --- Safety ---
        # Commands mentioning these words are never run without a spoken "yes".
        self.destructive_keywords = ("delete", "remove", "format", "shutdown", "restart", "reboot")
        self.confirm_words = ("yes", "confirm", "do it", "go ahead", "sure")
        self.cancel_words = ("no", "cancel", "stop", "nevermind", "never mind")

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent
