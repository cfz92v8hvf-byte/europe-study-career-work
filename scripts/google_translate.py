#!/usr/bin/env python3
"""Small, fail-closed adapter for Google Cloud Translation Basic (v2).

The adapter is intentionally not wired to publication.  It translates only
explicitly supplied text and refuses to use the final 10% of the monthly free
allowance, so a later queue worker must account for usage before every call.
"""
from __future__ import annotations

import json
import os
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://translation.googleapis.com/language/translate/v2"
MONTHLY_FREE_CAP = 500_000
SAFE_MONTHLY_CAP = 450_000


def _russian_text(payload: object) -> str:
    try:
        text = payload["data"]["translations"][0]["translatedText"].strip()  # type: ignore[index]
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        raise ValueError("Google Translation returned an invalid response") from error
    if len(text) < 2 or not any("а" <= char.lower() <= "я" for char in text):
        raise ValueError("Google Translation did not return Russian text")
    return text


def translate_to_russian(
    text: str,
    *,
    monthly_used_characters: int,
    api_key: str | None = None,
    opener: Callable[..., object] = urlopen,
) -> str:
    """Translate text using an explicitly configured Google API key.

    ``monthly_used_characters`` must come from the project's durable usage
    ledger.  This prevents a queue run from silently crossing the free tier.
    """
    text = text.strip()
    if not text:
        raise ValueError("Translation text is empty")
    if monthly_used_characters < 0:
        raise ValueError("Translation usage cannot be negative")
    if monthly_used_characters + len(text) > SAFE_MONTHLY_CAP:
        raise RuntimeError("Translation blocked: safe monthly free limit would be exceeded")
    key = api_key or os.getenv("GOOGLE_TRANSLATE_API_KEY")
    if not key:
        raise RuntimeError("Translation blocked: GOOGLE_TRANSLATE_API_KEY is not configured")

    body = urlencode({"q": text, "target": "ru", "format": "text", "key": key}).encode("utf-8")
    request = Request(API_URL, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with opener(request, timeout=20) as response:  # type: ignore[union-attr]
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as error:  # network/provider failures must stop the queue
        raise RuntimeError("Translation blocked: Google Translation request failed") from error
    return _russian_text(payload)
