"""Speech recognition module for Jarvis.

This class listens to the microphone and converts voice input into text.
It supports two backends:

1. Google Web Speech API via the `SpeechRecognition` package (default).
   No extra install needed, works out of the box, needs internet.
2. Faster-Whisper (optional, local, offline, usually more accurate).
   Only used if USE_FASTER_WHISPER=true in .env AND the `faster-whisper`
   package is installed. If it isn't installed, Jarvis quietly falls back
   to the Google backend instead of crashing.

It also adds wake-word listening ("Hey Jarvis") and continuous listening,
so Jarvis can run hands-free instead of needing a button press each time.
"""

from __future__ import annotations

from typing import Iterator, Optional

import speech_recognition as sr

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None


class SpeechRecognizer:
    """Object that captures microphone audio and converts it to text."""

    def __init__(self, use_faster_whisper: bool = False, whisper_model_size: str = "base.en") -> None:
        self.recognizer = None
        self.mic = None
        self._whisper_model = None
        self.backend = "google"

        try:
            self.recognizer = sr.Recognizer()
            # Tuned for faster, more reliable recognition than the library
            # defaults: less silence required before a phrase is considered
            # "done", and a higher noise floor so quiet rooms don't trigger
            # false starts.
            self.recognizer.pause_threshold = 1.0
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.dynamic_energy_adjustment_damping = 0.15
            self.recognizer.non_speaking_duration = 0.5

            device_index = self._get_default_microphone_index()
            self.mic = sr.Microphone(device_index=device_index)

            # Calibrate once at startup instead of before every single
            # listen() call -- this alone removes a big chunk of latency.
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
        except Exception as exc:
            self.recognizer = None
            self.mic = None
            print(f"Speech input initialization failed: {exc}")

        if use_faster_whisper:
            self._init_faster_whisper(whisper_model_size)

    def _init_faster_whisper(self, model_size: str) -> None:
        if WhisperModel is None:
            print(
                "USE_FASTER_WHISPER is enabled but the 'faster-whisper' package "
                "is not installed. Run: pip install faster-whisper\n"
                "Falling back to Google speech recognition for now."
            )
            return
        try:
            self._whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
            self.backend = "faster_whisper"
        except Exception as exc:
            print(f"Faster-Whisper failed to load ({exc}). Falling back to Google speech recognition.")
            self._whisper_model = None

    def _get_default_microphone_index(self) -> Optional[int]:
        """Return a usable microphone index when available."""
        try:
            devices = sr.Microphone.list_microphone_names()
            return 0 if devices else None
        except Exception:
            return None

    def _fallback_to_text_input(self) -> Optional[str]:
        """If speech capture is unavailable, allow keyboard-based commands."""
        print("Falling back to text input mode.")
        try:
            text = input("Type your command: ").strip()
        except EOFError:
            print("No input received. Exiting input loop.")
            return None
        except KeyboardInterrupt:
            print("Input cancelled.")
            return None
        return text or None

    def _transcribe(self, audio: sr.AudioData) -> Optional[str]:
        """Send captured audio to whichever backend is active and return text."""
        if self.backend == "faster_whisper" and self._whisper_model is not None:
            try:
                import io
                import wave

                buf = io.BytesIO(audio.get_wav_data())
                with wave.open(buf, "rb"):
                    pass  # validates the WAV data is readable
                buf.seek(0)
                segments, _ = self._whisper_model.transcribe(buf, vad_filter=True)
                text = " ".join(segment.text for segment in segments).strip()
                return text or None
            except Exception as exc:
                print(f"Faster-Whisper transcription failed ({exc}), trying Google instead.")

        try:
            for language in ("en-US", "ur-PK", "en-GB"):
                try:
                    text = self.recognizer.recognize_google(audio, language=language).strip()
                    if text:
                        return text
                except sr.UnknownValueError:
                    continue
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as exc:
            print(f"Speech recognition request failed: {exc}")
            return None

    def listen_and_recognize(self, timeout: float = 4, phrase_time_limit: float = 8) -> Optional[str]:
        """Listen to the microphone once and return recognized text.

        Uses a longer default listening window so natural, slightly longer
        sentences aren't cut off. Returns None (and falls back to typed
        input) if nothing usable was captured.
        """
        if self.recognizer is None or self.mic is None:
            return self._fallback_to_text_input()

        try:
            with self.mic as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = self._transcribe(audio)
            if text:
                return text
            return None
        except sr.WaitTimeoutError:
            return None
        except Exception as exc:
            print(f"Unexpected speech error: {exc}")
            return None

    def listen_stream(self) -> Iterator[str]:
        """Continuously yield recognized phrases until the caller stops iterating.

        This lets jarvis.py run a hands-free loop: `for phrase in recognizer.listen_stream():`
        instead of manually calling listen_and_recognize() over and over.
        """
        while True:
            text = self.listen_and_recognize(timeout=8, phrase_time_limit=10)
            if text:
                yield text

    def wait_for_wake_word(self, wake_words: list[str]) -> None:
        """Block quietly until one of the wake words (e.g. "hey jarvis") is heard."""
        if self.recognizer is None or self.mic is None:
            # No microphone available -- nothing to wait for, return immediately
            # so the caller falls back to typed input.
            return

        while True:
            try:
                with self.mic as source:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=4)
                text = self._transcribe(audio)
                if text and any(w in text.lower() for w in wake_words):
                    return
            except sr.WaitTimeoutError:
                continue
            except Exception:
                continue
