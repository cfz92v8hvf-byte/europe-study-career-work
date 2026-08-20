import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from queue_store import add_candidate, connect, review_capacity, transition
from operations_log import record


class QueueStoreTests(unittest.TestCase):
    def test_deduplicates_and_fails_closed_on_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            db = connect(Path(directory) / "queue.sqlite3")
            kwargs = dict(source_id="euraxess-jobs", source_url="https://euraxess.ec.europa.eu/jobs/offer/42", original_title="Research role")
            self.assertTrue(add_candidate(db, **kwargs))
            self.assertFalse(add_candidate(db, **kwargs))
            with self.assertRaises(ValueError):
                transition(db, 1, "published")

    def test_log_rejects_credential_named_fields(self):
        with self.assertRaises(ValueError):
            record("test", "ok", api_token="must-not-log")

    def test_rejects_non_official_candidate_url(self):
        with tempfile.TemporaryDirectory() as directory:
            db = connect(Path(directory) / "queue.sqlite3")
            with self.assertRaises(ValueError):
                add_candidate(db, source_id="euraxess-jobs", source_url="https://example.org/offer/42", original_title="Research role")

    def test_rejects_expired_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            db = connect(Path(directory) / "queue.sqlite3")
            with self.assertRaises(ValueError):
                add_candidate(
                    db,
                    source_id="euraxess-jobs",
                    source_url="https://euraxess.ec.europa.eu/jobs/offer/expired",
                    original_title="Expired research role",
                    deadline_at="2020-01-01T00:00:00+00:00",
                )

    def test_review_capacity_prevents_unbounded_accumulation(self):
        with tempfile.TemporaryDirectory() as directory:
            db = connect(Path(directory) / "queue.sqlite3")
            for index in range(review_capacity()):
                self.assertTrue(add_candidate(
                    db, source_id="euraxess-jobs",
                    source_url=f"https://euraxess.ec.europa.eu/jobs/offer/{index}",
                    original_title=f"Research role number {index}",
                ))
            with self.assertRaisesRegex(RuntimeError, "Review queue is full"):
                add_candidate(
                    db, source_id="euraxess-jobs",
                    source_url="https://euraxess.ec.europa.eu/jobs/offer/overflow",
                    original_title="Overflow research role",
                )


if __name__ == "__main__":
    unittest.main()
