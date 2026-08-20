from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from euraxess_adapter import discover_offer_urls


class EuraxessAdapterTests(unittest.TestCase):
    def test_keeps_only_direct_official_offers_and_deduplicates(self):
        html = """<a href="/jobs/123">A</a><a href="https://euraxess.ec.europa.eu/jobs/123">B</a>
        <a href="/jobs/search">search</a><a href="https://example.org/jobs/999">bad</a>"""
        self.assertEqual(discover_offer_urls(html), ["https://euraxess.ec.europa.eu/jobs/123"])


if __name__ == "__main__":
    unittest.main()
