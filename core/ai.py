"""Groq integration module for Jarvis.

This module is Jarvis's AI brain. Anything the local command router in
core/command_handler.py does not recognize gets sent here, so Jarvis can
answer questions, explain things, write code, and hold a natural
conversation instead of only understanding fixed commands.
"""

from __future__ import annotations

from collections import deque

try:
    from groq import Groq
except ModuleNotFoundError:
    Groq = None

from core.language import detect_language


# Jarvis's personality and priorities live here. Keeping the whole prompt in
# one place makes it easy to tweak how Jarvis "thinks" without touching any
# other file.
SYSTEM_PROMPT = """You are J.A.R.V.I.S., the user's personal AI operating system assistant.

How you behave:
- You prioritize being useful: if the user is asking a question, answer it well.
- Speak naturally, like a sharp, capable assistant. Never say "As an AI language model"
  or anything that sounds like a generic chatbot disclaimer.
- Keep spoken answers concise and direct (roughly 1-4 sentences) unless the user
  is asking for code, a document, or something that clearly needs more length.
- When asked for code, generate complete, correct, production-quality code with
  no placeholders or TODOs, inside a single fenced code block.
- Be professional, friendly, confident, calm, and intelligent. Never robotic.
- If you are unsure about something, say so briefly instead of guessing confidently.
- Match the user's language naturally. If the user speaks Urdu or mixed Urdu-English,
  reply in the same style unless they explicitly ask for English.
"""


class GroqAssistant:
    """Wrapper around Groq's chat API that also remembers recent turns."""

    def __init__(self, api_key: str, model_name: str = "llama-3.1-70b-versatile", max_memory_turns: int = 6, temperature: float = 0.4) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.client = None
        # Each entry is (user_text, jarvis_text). A deque automatically drops
        # the oldest turn once we go over the limit, so memory stays small.
        self.history: deque = deque(maxlen=max_memory_turns)

        if not api_key or Groq is None:
            return

        try:
            self.client = Groq(api_key=api_key)
        except Exception as exc:
            self.client = None
            print(f"Groq client initialization failed: {exc}")

    @property
    def is_available(self) -> bool:
        return self.client is not None

    def _build_context(self) -> str:
        """Turn recent history into a short block of context for follow-up questions."""
        if not self.history:
            return ""
        lines = []
        for user_text, jarvis_text in self.history:
            lines.append(f"User: {user_text}")
            lines.append(f"Jarvis: {jarvis_text}")
        return "Recent conversation:\n" + "\n".join(lines) + "\n\n"

    def _language_instruction(self, prompt: str) -> str:
        language = detect_language(prompt)
        if language == "ur":
            return "Reply naturally in Urdu. Keep the tone warm, direct, and human."
        if language == "mixed":
            return "Reply naturally in mixed Urdu-English (Urdulish), matching the user's style."
        return "Reply naturally in English. Keep the tone warm, direct, and human."

    def ask(self, prompt: str, remember: bool = True) -> str:
        """Ask Groq a question (with recent conversation context) and return the reply text."""
        if not self.api_key:
            return "Groq API key is missing. Please add GROQ_API_KEY to your .env file."

        if self.client is None:
            return "Groq is not available right now. Check that the groq package is installed and your API key is valid."

        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            context = self._build_context().strip()
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "system", "content": self._language_instruction(prompt)})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
            )
            text = (response.choices[0].message.content or "").strip()
            if not text:
                text = "I could not generate a response for that."
            if remember:
                self.history.append((prompt, text))
            return text
        except Exception as exc:
            return f"I ran into an issue reaching my AI core: {exc}"

    def generate_code(self, task: str, language: str = "") -> str:
        """Ask Groq for code only, and return just the code (fences stripped).

        Used by commands/coder.py so generated code can be saved straight to a file.
        """
        if self.client is None:
            return ""

        lang_hint = f" in {language}" if language else ""
        prompt = (
            f"Write complete, working, production-quality code{lang_hint} for this task: {task}\n"
            "Return ONLY the code in a single fenced code block, with no explanation before or after."
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=max(0.1, min(self.temperature, 0.2)),
            )
            text = (response.choices[0].message.content or "").strip()
        except Exception as exc:
            return f"# Code generation failed: {exc}"

        return self._strip_code_fence(text)

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        """Remove ```language ... ``` fencing if the model wrapped the code in one."""
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines:
                lines = lines[1:]  # drop opening ```lang line
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]  # drop closing ```
            return "\n".join(lines).strip()
        return stripped
