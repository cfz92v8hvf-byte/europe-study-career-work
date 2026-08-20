"""Create compact Russian Telegram cards while preserving the primary source."""
from __future__ import annotations

import re
from urllib.parse import urlparse

MAX_SUMMARY = 700


def _has_cyrillic(text: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", text))


def format_post(*, title_ru: str, summary_ru: str, source_name: str, source_url: str,
                deadline_label: str | None = None) -> str:
    """Fail closed unless a Russian summary and an official source link are present."""
    title = title_ru.strip()
    summary = summary_ru.strip()
    parsed = urlparse(source_url)
    if not title or not summary or not _has_cyrillic(title + summary):
        raise ValueError("A Russian title and summary are required before publication")
    if len(summary) > MAX_SUMMARY:
        raise ValueError("Russian summary exceeds the compact-post limit")
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("A direct HTTPS source URL is required")
    deadline = f"\n\n⏳ Срок: {deadline_label.strip()}" if deadline_label and deadline_label.strip() else ""
    return f"<b>{title}</b>\n\n{summary}{deadline}\n\n🔗 <a href=\"{source_url}\">{source_name.strip()}</a>"
