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


def extract_offer_title(html: str) -> str:
    """Return an offer title from a fetched official offer page without translating it."""
    patterns = (
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
        r"<title[^>]*>(.*?)</title>",
    )
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.I | re.S)
        if match:
            title = re.sub(r"\s+", " ", unescape(match.group(1))).strip()
            if len(title) >= 8:
                return title
    raise RuntimeError("EURAXESS offer page has no usable title")


def extract_offer_summary(html: str) -> str | None:
    """Extract only an official page description suitable for later human review."""
    patterns = (
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
    )
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.I | re.S)
        if match:
            text = re.sub(r"\s+", " ", unescape(match.group(1))).strip()
            raw = text.encode("utf-8")
            if len(raw) <= 450:
                short = text
            else:
                short = raw[:450].decode("utf-8", errors="ignore").rsplit(" ", 1)[0].strip()
            if len(short) >= 40:
                return short
    return None


def fetch_offer_title(url: str) -> str:
    return fetch_offer_details(url)[0]


def fetch_offer_details(url: str) -> tuple[str, str | None]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != HOST or not re.fullmatch(r"/jobs/\d+", parsed.path):
        raise ValueError("Only direct EURAXESS offer URLs may be fetched")
    request = Request(url, headers={"User-Agent": "EuropeStudyCareerReviewBot/1.0"})
    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError("EURAXESS offer page did not return HTTP 200")
        html = response.read().decode("utf-8", errors="replace")
        return extract_offer_title(html), extract_offer_summary(html)


if __name__ == "__main__":
    print("\n".join(discover_offer_urls(fetch_search_html())[:20]))
