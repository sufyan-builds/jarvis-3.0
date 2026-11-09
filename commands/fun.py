"""Fun and motivational content commands for Jarvis.

This module gives the assistant fun responses such as jokes and quotes.
"""

from __future__ import annotations

import random

import pyjokes


class FunCommands:
    """Provide light entertainment and motivation."""

    def tell_joke(self) -> str:
        """Return a random joke using pyjokes."""
        return pyjokes.get_joke()

    def motivational_quote(self) -> str:
        """Return a motivational quote from a built-in list."""
        quotes = [
            "Success is the sum of small efforts, repeated day in and day out.",
            "You are capable of amazing things.",
            "Keep going. Your future self will thank you.",
            "Every step forward counts.",
            "Believe in yourself and stay consistent.",
        ]
        return random.choice(quotes)
