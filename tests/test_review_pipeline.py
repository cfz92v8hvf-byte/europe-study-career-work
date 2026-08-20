from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import review_pipeline
from queue_store import add_candidate, connect


class ReviewPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tempdir.name) / "queue.sqlite3")

    def tearDown(self):
        self.db.close()
        self.tempdir.cleanup()

    def test_collects_and_translates_without_publication(self):
        def collector(limit, *, enqueue):
            self.assertTrue(enqueue)
            self.assertEqual(limit, 3)
            add_candidate(self.db, source_id="euraxess-jobs", source_url="https://euraxess.ec.europa.eu/jobs/123", original_title="Research assistant position")
            return [{"added_to_review": True}]

        def translator(db, *, limit):
            self.assertEqual(limit, 3)
            db.execute("UPDATE candidates SET title_ru='Должность научного сотрудника' WHERE id=1")
            db.commit()
            return 1

        with patch.object(review_pipeline, "record"):
            result = review_pipeline.run(collector=collector, translator=translator, db=self.db)
        self.assertEqual(result, {"review_slots": 12, "collected": 1, "translated": 1, "summaries_translated": 0, "audited": 1})
        self.assertEqual(self.db.execute("SELECT status FROM candidates").fetchone()[0], "review")

    def test_stops_collection_when_review_queue_is_full(self):
        for number in range(12):
            add_candidate(self.db, source_id="euraxess-jobs", source_url=f"https://euraxess.ec.europa.eu/jobs/{number}", original_title=f"Research assistant position {number}", title_ru=f"Должность научного сотрудника {number}")

        with patch.object(review_pipeline, "record"):
            result = review_pipeline.run(collector=lambda *_args, **_kwargs: self.fail("must not collect"), translator=lambda *_args, **_kwargs: self.fail("must not translate"), db=self.db)
        self.assertEqual(result, {"review_slots": 0, "collected": 0, "translated": 0, "summaries_translated": 0, "audited": 12})
