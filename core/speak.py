"""Text-to-speech module for Jarvis.

This class uses pyttsx3 to speak responses back to the user.

Note on design: pyttsx3's SAPI5 driver (used on Windows) has a well-known
bug where reusing a single engine instance across multiple say()/runAndWait()
calls in the same process often speaks correctly exactly once, then goes
silent on every call after that. To guarantee Jarvis actually speaks every
single reply, a fresh lightweight engine is created for each speak() call.
Initializing pyttsx3 only takes a fraction of a second, so this trade-off
(slightly more setup time, in exchange for reliable audio every time) is
worth it.
"""

from __future__ import annotations

import threading

import pyttsx3

from core.language import detect_language


class TextToSpeech:
    """Simple wrapper around the system text-to-speech engine."""

    def __init__(self, rate: int = 185, volume: float = 1.0) -> None:
        self.rate = rate
        self.volume = volume
        self._lock = threading.Lock()
        self.engine = None  # kept for compatibility checks elsewhere (e.g. app.py status pill)
        self._default_voice_id = None
        self._english_voice_id = None
        self._urdu_voice_id = None

        # Do one throwaway init at startup purely to confirm TTS works on
        # this machine and to surface a clear error immediately if not.
        try:
            test_engine = pyttsx3.init()
            voices = list(test_engine.getProperty("voices") or [])
            if voices:
                self._default_voice_id = voices[0].id
                for voice in voices:
                    voice_blob = self._voice_blob(voice)
                    if self._english_voice_id is None and ("english" in voice_blob or "en" in voice_blob):
                        self._english_voice_id = voice.id
                    if self._urdu_voice_id is None and ("urdu" in voice_blob or "ur" in voice_blob):
                        self._urdu_voice_id = voice.id
            test_engine.stop()
            self.engine = True
        except Exception as exc:
            print(f"Text-to-speech initialization failed: {exc}")
            self.engine = None

    @staticmethod
    def _voice_blob(voice: object) -> str:
        parts = []
        for attribute in ("id", "name"):
            value = getattr(voice, attribute, "")
            if value:
                parts.append(str(value))
        for value in getattr(voice, "languages", []) or []:
            if isinstance(value, bytes):
                try:
                    parts.append(value.decode("utf-8", errors="ignore"))
                except Exception:
                    parts.append(str(value))
            else:
                parts.append(str(value))
        return " ".join(parts).lower()

    def _voice_id_for_text(self, text: str) -> str | None:
        language = detect_language(text)
        if language in {"ur", "mixed"} and self._urdu_voice_id:
            return self._urdu_voice_id
        if self._english_voice_id:
            return self._english_voice_id
        return self._default_voice_id

    def speak(self, text: str) -> None:
        """Speak a provided string to the user and wait until it finishes."""
        text = (text or "").strip()
        if not text:
            return

        if self.engine is None:
            print(f"Jarvis: {text}")
            return

        try:
            # A lock keeps overlapping speak() calls from fighting over
            # audio output if two threads ever call it at once.
            with self._lock:
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
                voice_id = self._voice_id_for_text(text)
                if voice_id:
                    engine.setProperty("voice", voice_id)
                language = detect_language(text)
                if language in {"ur", "mixed"}:
                    engine.setProperty("rate", max(140, self.rate - 20))
                engine.say(text)
                engine.runAndWait()
                engine.stop()
        except Exception as exc:
            print(f"Text-to-speech playback failed: {exc}")
            print(f"Jarvis: {text}")

    def speak_async(self, text: str) -> None:
        """Speak without blocking the caller (e.g. so the UI can update immediately)."""
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()
