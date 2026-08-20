"""Review-only discovery of direct offer URLs from the official EURAXESS search page."""
from __future__ import annotations

import re
from html import unescape
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

SEARCH_URL = "https://euraxess.ec.europa.eu/jobs/search"
HOST = "euraxess.ec.europa.eu"


def discover_offer_urls(html: str) -> list[str]:
    urls: list[str] = []
    for href in re.findall(r'href=["\']([^"\']+)["\']', unescape(html), flags=re.I):
        url = urljoin(SEARCH_URL, href)
        parsed = urlparse(url)
        if parsed.scheme == "https" and parsed.hostname == HOST and re.fullmatch(r"/jobs/\d+", parsed.path):
            if url not in urls:
                urls.append(url)
    return urls


def fetch_search_html() -> str:
    request = Request(SEARCH_URL, headers={"User-Agent": "EuropeStudyCareerReviewBot/1.0"})
    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError("EURAXESS search page did not return HTTP 200")
        return response.read().decode("utf-8", errors="replace")


if __name__ == "__main__":
    print("\n".join(discover_offer_urls(fetch_search_html())[:20]))
