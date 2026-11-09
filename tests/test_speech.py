import unittest
from unittest.mock import patch

from core.speech import SpeechRecognizer


class SpeechRecognizerTests(unittest.TestCase):
    def test_listen_and_recognize_returns_none_on_eof(self):
        recognizer = SpeechRecognizer.__new__(SpeechRecognizer)  # skip real mic init
        recognizer.recognizer = None
        recognizer.mic = None
        recognizer._whisper_model = None
        recognizer.backend = "google"

        with patch("builtins.input", side_effect=EOFError):
            result = recognizer.listen_and_recognize()

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
