"""Fail-closed contract for a future Russian translation provider."""
from __future__ import annotations

import json


def build_request(*, original_title: str, source_url: str) -> str:
    if not original_title.strip() or not source_url.startswith("https://"):
        raise ValueError("Translation request requires an original title and official HTTPS URL")
    return json.dumps({
        "task": "Translate the opportunity title into concise Russian.",
        "rules": [
            "Return JSON only with key title_ru.",
            "Do not add facts, deadlines, eligibility claims, amounts, or links.",
            "Keep names of institutions and programmes when needed for accuracy.",
            "Use Russian Cyrillic and no marketing language.",
        ],
        "original_title": original_title.strip(),
        "source_url": source_url,
    }, ensure_ascii=False)


def parse_response(payload: str) -> str:
    try:
        title = json.loads(payload)["title_ru"].strip()
    except (json.JSONDecodeError, KeyError, AttributeError) as error:
        raise ValueError("Translation provider returned an invalid response") from error
    if len(title) < 8 or not any("а" <= char.lower() <= "я" for char in title):
        raise ValueError("Translation provider did not return a Russian title")
    return title
