import unittest
from unittest.mock import Mock, patch

from commands.browser import BrowserCommands


class BrowserCommandTests(unittest.TestCase):
    @patch("commands.browser.webbrowser.open")
    @patch("commands.browser.requests.get")
    def test_open_youtube_first_result_opens_video(self, mock_get, mock_open):
        response = Mock()
        response.raise_for_status.return_value = None
        response.text = '{"videoId":"abc123"}{"videoId":"def456"}'
        mock_get.return_value = response

        browser = BrowserCommands()
        result = browser.open_youtube_first_result("Believer")

        self.assertEqual(result, "Playing Believer on YouTube.")
        mock_open.assert_called_once_with("https://www.youtube.com/watch?v=abc123&autoplay=1")

    @patch("commands.browser.webbrowser.open")
    @patch("commands.browser.requests.get", side_effect=Exception("network down"))
    def test_open_youtube_first_result_falls_back_to_search(self, mock_get, mock_open):
        browser = BrowserCommands()
        result = browser.open_youtube_first_result("Believer")

        self.assertEqual(result, "Opening YouTube search results for Believer.")
        mock_open.assert_called_once()


if __name__ == "__main__":
    unittest.main()
