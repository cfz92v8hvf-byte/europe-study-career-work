from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import telegram_publish


class TelegramPublisherTests(unittest.TestCase):
    def test_test_message_is_clearly_marked(self):
        self.assertIn("#тест_автоматизации", telegram_publish.test_message())

    def test_default_run_is_dry(self):
        original = sys.argv
        try:
            sys.argv = ["telegram_publish.py"]
            self.assertEqual(telegram_publish.main(), 0)
        finally:
            sys.argv = original


if __name__ == "__main__":
    unittest.main()
