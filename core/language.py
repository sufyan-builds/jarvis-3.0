"""Shared language helpers for Jarvis.

These helpers keep bilingual and mixed Urdu-English support consistent across
speech recognition, command routing, AI responses, and text-to-speech.
"""

from __future__ import annotations

import re

URDU_SCRIPT_RE = re.compile(r"[\u0600-\u06FF]")
LATIN_WORD_RE = re.compile(r"[a-z]+", re.IGNORECASE)

_COMMAND_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bkhol(?:o| do|na)?\b", "open"),
    (r"\bkholo\b", "open"),
    (r"\bchalao\b", "play"),
    (r"\bbanao\b", "create"),
    (r"\bdhoond(?:o|ho)\b", "search"),
    (r"\bdhundho\b", "search"),
    (r"\btalash\b", "search"),
    (r"\bhatao\b", "delete"),
    (r"\bkhatam karo\b", "close"),
    (r"\bband karo\b", "close"),
    (r"\bbarhao\b", "up"),
    (r"\bbadhao\b", "up"),
    (r"\bghatao\b", "down"),
    (r"\bkam karo\b", "down"),
    (r"\brestart karo\b", "restart"),
    (r"\bshutdown karo\b", "shutdown"),
    (r"\bshut down karo\b", "shutdown"),
    (r"\bscreenshot le lo\b", "screenshot"),
    (r"\bscreen shot le lo\b", "screenshot"),
    (r"\bcopy karo\b", "copy"),
    (r"\bmove karo\b", "move"),
    (r"\bdelete karo\b", "delete"),
)

_ROMAN_URDU_MARKERS = (
    "khol", "kholo", "chalao", "banao", "dhoondo", "dhundo", "talash",
    "hatao", "barhao", "badhao", "ghatao", "kam karo", "restart karo",
    "shutdown karo", "screenshot le lo", "le lo", "mujhe", "mera", "karo",
)


def contains_urdu_script(text: str) -> bool:
    return bool(URDU_SCRIPT_RE.search(text or ""))


def detect_language(text: str) -> str:
    """Return 'en', 'ur', or 'mixed' using a lightweight heuristic."""
    sample = (text or "").strip()
    if not sample:
        return "en"

    has_urdu_script = contains_urdu_script(sample)
    has_latin = bool(LATIN_WORD_RE.search(sample))

    if has_urdu_script and has_latin:
        return "mixed"
    if has_urdu_script:
        return "ur"

    lowered = sample.lower()
    has_roman_urdu = any(marker in lowered for marker in _ROMAN_URDU_MARKERS)
    if has_roman_urdu and has_latin:
        return "mixed"
    if has_roman_urdu:
        return "ur"
    return "en"


def normalize_command_text(text: str) -> str:
    """Normalize English, Urdu-script, and Roman Urdu commands for routing."""
    normalized = (text or "").lower()
    normalized = normalized.replace("?", " ").replace("!", " ")
    normalized = re.sub(r"\.(?=\s|$)", " ", normalized)
    normalized = re.sub(r"[,;:()\[\]{}]", " ", normalized)

    for pattern, replacement in _COMMAND_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized
