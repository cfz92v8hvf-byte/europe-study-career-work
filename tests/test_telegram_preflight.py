from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from telegram_preflight import can_publish


class TelegramPreflightTests(unittest.TestCase):
    def test_requires_administrator_and_post_permission(self):
        self.assertTrue(can_publish({"status": "administrator", "can_post_messages": True}))
        self.assertFalse(can_publish({"status": "member"}))
        self.assertFalse(can_publish({"status": "administrator", "can_post_messages": False}))


if __name__ == "__main__":
    unittest.main()
