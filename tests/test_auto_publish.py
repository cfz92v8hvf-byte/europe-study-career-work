from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import auto_publish
from queue_store import add_candidate, connect


class AutoPublishTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tempdir.name) / "queue.sqlite3")

    def tearDown(self):
        self.db.close()
        self.tempdir.cleanup()

    def test_publishes_one_checked_card_and_saves_receipt(self):
        add_candidate(
            self.db,
            source_id="euraxess-jobs",
            source_url="https://euraxess.ec.europa.eu/jobs/999",
            original_title="Research assistant position",
            title_ru="Должность научного сотрудника",
            summary_ru="Официальное объявление о возможности. Условия приведены по прямой ссылке.",
        )
        sent = []
        with patch.object(auto_publish, "record"), patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test-token", "TELEGRAM_CHANNEL": "@test-channel"}):
            result = auto_publish.publish_one(
                db=self.db,
                now=datetime(2026, 8, 20, tzinfo=timezone.utc),
                preflight_check=lambda: None,
                sender=lambda token, channel, message: sent.append(message) or 77,
            )
        self.assertEqual(result, {"bootstrapped": 0, "published": 1})
        self.assertEqual(len(sent), 1)
        row = self.db.execute("SELECT status, telegram_message_id FROM candidates").fetchone()
        self.assertEqual((row["status"], row["telegram_message_id"]), ("published", 77))

    def test_bootstrap_prevents_a_manual_link_from_being_sent_again(self):
        add_candidate(
            self.db,
            source_id="euraxess-jobs",
            source_url="https://euraxess.ec.europa.eu/jobs/461017",
            original_title="Research assistant position",
            title_ru="Должность научного сотрудника",
            summary_ru="Официальное объявление о возможности. Условия приведены по прямой ссылке.",
        )
        with patch.object(auto_publish, "record"):
            result = auto_publish.publish_one(
                db=self.db,
                now=datetime(2026, 8, 20, tzinfo=timezone.utc),
                preflight_check=lambda: self.fail("must not publish"),
                sender=lambda *_: self.fail("must not send"),
            )
        self.assertEqual(result, {"bootstrapped": 1, "published": 0})
        self.assertEqual(self.db.execute("SELECT status FROM candidates").fetchone()[0], "published")


if __name__ == "__main__":
    unittest.main()
