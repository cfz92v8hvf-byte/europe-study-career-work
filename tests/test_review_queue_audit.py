from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from queue_store import add_candidate, connect
from review_queue_audit import audit


class ReviewQueueAuditTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tempdir.name) / "queue.sqlite3")

    def tearDown(self):
        self.db.close()
        self.tempdir.cleanup()

    def test_accepts_valid_translated_review_card(self):
        add_candidate(self.db, source_id="euraxess-jobs", source_url="https://euraxess.ec.europa.eu/jobs/1", original_title="Research assistant position", title_ru="Должность научного сотрудника")
        self.assertEqual(audit(self.db), 1)

    def test_blocks_untranslated_review_card(self):
        add_candidate(self.db, source_id="euraxess-jobs", source_url="https://euraxess.ec.europa.eu/jobs/1", original_title="Research assistant position")
        with self.assertRaisesRegex(RuntimeError, "untranslated"):
            audit(self.db)

    def test_blocks_known_academic_title_mistranslation(self):
        add_candidate(self.db, source_id="euraxess-jobs", source_url="https://euraxess.ec.europa.eu/jobs/2", original_title="PhD Candidate in Materials", title_ru="Кандидат наук в области материалов")
        with self.assertRaisesRegex(RuntimeError, "PhD Candidate"):
            audit(self.db)
