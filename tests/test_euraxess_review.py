from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import euraxess_review


class EuraxessReviewTests(unittest.TestCase):
    @patch("euraxess_review.fetch_offer_title", side_effect=["Official role one", "Official role two"])
    @patch("euraxess_review.discover_offer_urls", return_value=["https://euraxess.ec.europa.eu/jobs/1", "https://euraxess.ec.europa.eu/jobs/2"])
    @patch("euraxess_review.fetch_search_html", return_value="page")
    def test_default_collection_does_not_write_queue(self, _html, _urls, _titles):
        rows = euraxess_review.collect(2)
        self.assertEqual([row["added_to_review"] for row in rows], [None, None])

    def test_limit_is_bounded(self):
        with self.assertRaises(ValueError):
            euraxess_review.collect(0)
        with self.assertRaises(ValueError):
            euraxess_review.collect(21)

    @patch("euraxess_review.fetch_offer_title", side_effect=RuntimeError("rate limited"))
    @patch("euraxess_review.discover_offer_urls", return_value=["https://euraxess.ec.europa.eu/jobs/1"])
    @patch("euraxess_review.fetch_search_html", return_value="page")
    def test_temporary_source_error_does_not_stop_collection(self, _html, _urls, _title):
        row = euraxess_review.collect(1)[0]
        self.assertEqual(row["added_to_review"], None)
        self.assertEqual(row["error"], "official page unavailable: RuntimeError")


if __name__ == "__main__":
    unittest.main()
