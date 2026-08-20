from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from queue_store import add_candidate, connect
from translate_review_titles import pending_titles, translate_pending


class ReviewTitleTranslationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tempdir.name) / "queue.sqlite3")
        add_candidate(self.db, source_id="euraxess-jobs", source_url="https://euraxess.ec.europa.eu/jobs/123", original_title="Research assistant position")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_dry_selection_keeps_title_untranslated(self):
        self.assertEqual(len(pending_titles(self.db, 3)), 1)
        self.assertIsNone(self.db.execute("SELECT title_ru FROM candidates").fetchone()[0])

    def test_translation_updates_review_title_only(self):
        calls = []
        def fake_translator(db, title):
            calls.append(title)
            return "Должность научного сотрудника"

        self.assertEqual(translate_pending(self.db, translator=fake_translator), 1)
        row = self.db.execute("SELECT title_ru, status FROM candidates").fetchone()
        self.assertEqual(calls, ["Research assistant position"])
        self.assertEqual(row[0], "Должность научного сотрудника")
        self.assertEqual(row[1], "review")
