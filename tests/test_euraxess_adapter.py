from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from euraxess_adapter import discover_offer_urls, extract_offer_title


class EuraxessAdapterTests(unittest.TestCase):
    def test_keeps_only_direct_official_offers_and_deduplicates(self):
        html = """<a href="/jobs/123">A</a><a href="https://euraxess.ec.europa.eu/jobs/123">B</a>
        <a href="/jobs/search">search</a><a href="https://example.org/jobs/999">bad</a>"""
        self.assertEqual(discover_offer_urls(html), ["https://euraxess.ec.europa.eu/jobs/123"])

    def test_prefers_open_graph_title_and_falls_back_to_page_title(self):
        self.assertEqual(
            extract_offer_title('<meta property="og:title" content="Research assistant &amp; trainee">'),
            "Research assistant & trainee",
        )
        self.assertEqual(extract_offer_title("<title>Official opportunity page</title>"), "Official opportunity page")


if __name__ == "__main__":
    unittest.main()
