"""Autonomous J.A.R.V.I.S. Core with a cyberpunk terminal UI.

Run with:  python jarvis.py

Jarvis wakes on a wake word (default "hey jarvis" or just "jarvis"), then
keeps listening continuously and executing commands until you say an exit
phrase like "goodbye" or press Ctrl+C.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from config import Config
from core.ai import GroqAssistant
from core.command_handler import CommandHandler
from core.speak import TextToSpeech
from core.speech import SpeechRecognizer

console = Console()


class JarvisEngine:
    """Ties speech input, the command handler, and speech output together."""

    def __init__(self) -> None:
        self.config = Config()

        # Every expensive object (TTS engine, AI model, mic calibration) is
        # created exactly once here and reused for the whole session.
        self.tts = TextToSpeech()
        self.ai = GroqAssistant(
            api_key=self.config.groq_api_key,
            model_name=self.config.groq_model,
            max_memory_turns=self.config.max_memory_turns,
            temperature=self.config.ai_temperature,
        )
        self.speech = SpeechRecognizer(
            use_faster_whisper=self.config.use_faster_whisper,
            whisper_model_size=self.config.whisper_model_size,
        )
        self.handler = CommandHandler(self.tts, self.ai)

    def speak(self, text: str) -> None:
        console.print(Panel(Text(f"J.A.R.V.I.S.: {text}", style="bold cyan"), title="SYSTEM OUTPUT", border_style="cyan"))
        self.tts.speak(text)

    def run(self) -> None:
        console.clear()
        console.print(Panel.fit(
            "[bold bright_cyan]J.A.R.V.I.S. AUTONOMOUS CORE ACTIVATED[/]\n"
            f"[dim]Say \"{self.config.wake_words[0]}\" to wake me up, or Ctrl+C to quit.[/]",
            border_style="bright_blue",
        ))

        try:
            while True:
                self.speech.wait_for_wake_word(self.config.wake_words)
                self.speak("Yes? I'm listening.")
                self._conversation_loop()
                console.print("[dim]Going back to sleep. Say the wake word to talk to me again.[/]")
        except KeyboardInterrupt:
            self.speak("Manual override detected. Terminating process.")

    def _conversation_loop(self) -> None:
        """Keep handling commands until exit or inactivity returns to wake mode."""
        import time

        inactive_since = time.monotonic()
        sleep_after_seconds = self.config.sleep_after_seconds

        while True:
            command = self.speech.listen_and_recognize(timeout=6, phrase_time_limit=8)
            if not command:
                if time.monotonic() - inactive_since >= sleep_after_seconds:
                    return
                continue

            inactive_since = time.monotonic()
            console.print(f"[bold yellow]YOU SAID:[/] {command}")
            try:
                response = self.handler.handle_command(command)
            except Exception as exc:
                # Never crash and never show a raw traceback to the user.
                console.print(f"[bold red]Internal error:[/] {exc}")
                self.speak("Sorry, I ran into an unexpected problem with that. Let's try something else.")
                continue

            if response is None:
                self.speak("Shutting down J.A.R.V.I.S. systems. Goodbye, sir.")
                raise SystemExit(0)

            self.speak(response)


if __name__ == "__main__":
    try:
        JarvisEngine().run()
    except SystemExit:
        pass
