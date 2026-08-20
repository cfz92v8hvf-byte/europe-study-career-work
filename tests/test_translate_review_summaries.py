from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from queue_store import add_candidate, connect
from translate_review_summaries import translate_pending_summaries

class SummaryTranslationTests(unittest.TestCase):
    def test_updates_only_official_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            db = connect(Path(temp) / "q.sqlite3")
            add_candidate(db, source_id="euraxess-jobs", source_url="https://euraxess.ec.europa.eu/jobs/1", original_title="Research assistant position", original_summary="Official European research opportunity with funded mobility support and laboratory mentoring.")
            self.assertEqual(translate_pending_summaries(db, translator=lambda _db, _text: "Официальная исследовательская возможность с поддержкой мобильности и наставничеством."), 1)
            self.assertIn("Официальная", db.execute("SELECT summary_ru FROM candidates").fetchone()[0])
