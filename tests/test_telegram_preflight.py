from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from telegram_preflight import api, can_publish


class TelegramPreflightTests(unittest.TestCase):
    def test_requires_administrator_and_post_permission(self):
        self.assertTrue(can_publish({"status": "administrator", "can_post_messages": True}))
        self.assertFalse(can_publish({"status": "member"}))
        self.assertFalse(can_publish({"status": "administrator", "can_post_messages": False}))

    @patch("telegram_preflight.urlopen", side_effect=HTTPError("url", 400, "bad request", {}, None))
    def test_classifies_unavailable_bot_as_safe_block(self, _urlopen):
        with self.assertRaisesRegex(RuntimeError, "not available as a channel administrator"):
            api("token", "getChatMember", {"chat_id": "@channel", "user_id": 1})


if __name__ == "__main__":
    unittest.main()
