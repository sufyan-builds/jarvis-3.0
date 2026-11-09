"""Browser search commands for Jarvis.

This module opens search results in the default browser.
"""

from __future__ import annotations

import re
import webbrowser
from urllib.parse import quote_plus

import requests

from config import Config


class BrowserCommands:
    """Wrap browser-related operations."""

    def __init__(self) -> None:
        self.config = Config()

    def search_google(self, query: str) -> str:
        """Search Google for a user query."""
        url = f"{self.config.google_search_url}{quote_plus(query)}"
        webbrowser.open(url)
        return f"Searching Google for {query}."

    def search_youtube(self, query: str) -> str:
        """Search YouTube for a user query."""
        url = f"{self.config.youtube_url}{quote_plus(query)}"
        webbrowser.open(url)
        return f"Searching YouTube for {query}."

    def open_youtube_first_result(self, query: str) -> str:
        """Open the first likely YouTube video result for a query.

        Falls back to the search results page if YouTube blocks the request or
        if the page markup changes.
        """
        search_url = f"{self.config.youtube_url}{quote_plus(query)}"
        try:
            response = requests.get(
                "https://www.youtube.com/results",
                params={"search_query": query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=8,
            )
            response.raise_for_status()

            video_ids = []
            for match in re.finditer(r'"videoId":"([^"]+)"', response.text):
                video_id = match.group(1)
                if video_id not in video_ids:
                    video_ids.append(video_id)
                if len(video_ids) >= 5:
                    break

            if video_ids:
                webbrowser.open(f"https://www.youtube.com/watch?v={video_ids[0]}&autoplay=1")
                return f"Playing {query} on YouTube."
        except Exception:
            pass

        webbrowser.open(search_url)
        return f"Opening YouTube search results for {query}."

    def search_github(self, query: str) -> str:
        """Search GitHub for a user query."""
        url = f"https://github.com/search?q={quote_plus(query)}"
        webbrowser.open(url)
        return f"Searching GitHub for {query}."

    def search_stackoverflow(self, query: str) -> str:
        """Search Stack Overflow for a user query."""
        url = f"https://stackoverflow.com/search?q={quote_plus(query)}"
        webbrowser.open(url)
        return f"Searching Stack Overflow for {query}."
