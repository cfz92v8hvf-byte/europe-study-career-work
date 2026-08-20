#!/usr/bin/env python3
"""Separate free translation path modelled on Politikan, with stricter guards.

It has no shared imports, URLs, credentials, database, or queue state with
Politikan.  The public MyMemory endpoint is used only for short English titles;
the caller must review each resulting candidate before publication.
"""
from __future__ import annotations

import html
import json
from datetime import date
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://api.mymemory.translated.net/get"
MAX_SOURCE_BYTES = 500
SAFE_DAILY_CAP = 4_000


def _ensure_usage_table(db) -> None:
    db.execute("""CREATE TABLE IF NOT EXISTS translation_usage (
        usage_day TEXT PRIMARY KEY,
        characters_used INTEGER NOT NULL CHECK(characters_used >= 0)
    )""")
    db.commit()


def used_today(db, today: date | None = None) -> int:
    _ensure_usage_table(db)
    day = (today or date.today()).isoformat()
    row = db.execute("SELECT characters_used FROM translation_usage WHERE usage_day=?", (day,)).fetchone()
    return int(row[0]) if row else 0


def _record_usage(db, characters: int, today: date | None = None) -> None:
    day = (today or date.today()).isoformat()
    db.execute("""INSERT INTO translation_usage(usage_day, characters_used) VALUES (?, ?)
        ON CONFLICT(usage_day) DO UPDATE SET characters_used=characters_used + excluded.characters_used""", (day, characters))
    db.commit()


def _parse_translation(payload: object) -> str:
    try:
        result = payload["responseData"]  # type: ignore[index]
        text = html.unescape(result["translatedText"]).strip()
        status = payload["responseStatus"]  # type: ignore[index]
        score = float(result.get("match", 0))
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ValueError("MyMemory returned an invalid translation response") from error
    if status != 200 or score < 0.70:
        raise ValueError("MyMemory translation did not meet the review threshold")
    if len(text) < 2 or not any("а" <= char.lower() <= "я" for char in text):
        raise ValueError("MyMemory did not return Russian text")
    return text


def translate_en_title_to_russian(db, text: str, *, opener: Callable[..., object] = urlopen) -> str:
    """Translate a short English title and record only successful daily usage."""
    text = text.strip()
    source_bytes = text.encode("utf-8")
    if not text or len(source_bytes) > MAX_SOURCE_BYTES:
        raise ValueError("MyMemory accepts only non-empty titles up to 500 UTF-8 bytes")
    usage = used_today(db)
    if usage + len(text) > SAFE_DAILY_CAP:
        raise RuntimeError("Translation blocked: safe daily free limit would be exceeded")
    query = urlencode({"q": text, "langpair": "en|ru"})
    request = Request(f"{API_URL}?{query}", headers={"User-Agent": "EuropeStudyCareer/1.0"})
    try:
        with opener(request, timeout=20) as response:  # type: ignore[union-attr]
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        raise RuntimeError("Translation blocked: MyMemory request failed") from error
    translated = _parse_translation(payload)
    _record_usage(db, len(text))
    return translated
