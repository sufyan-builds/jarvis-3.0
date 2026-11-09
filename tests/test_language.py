import unittest

from core.language import detect_language, normalize_command_text


class LanguageHelperTests(unittest.TestCase):
    def test_detect_language_english(self):
        self.assertEqual(detect_language("Open Chrome"), "en")

    def test_detect_language_urdu_script(self):
        self.assertEqual(detect_language("کروم کھولو"), "ur")

    def test_detect_language_mixed(self):
        self.assertEqual(detect_language("Chrome kholo"), "mixed")

    def test_normalize_command_text_translates_common_phrases(self):
        normalized = normalize_command_text("Chrome kholo")
        self.assertIn("open", normalized)
        self.assertIn("chrome", normalized)


if __name__ == "__main__":
    unittest.main()
