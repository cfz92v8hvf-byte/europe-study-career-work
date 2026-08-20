"""Validation boundary between official sources and the publication queue."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def _registry() -> dict[str, dict]:
    data = json.loads((ROOT / "config" / "sources.json").read_text(encoding="utf-8"))
    return {source["id"]: source for source in data["sources"]}


def validate_candidate(*, source_id: str, source_url: str, original_title: str,
                       deadline_at: str | None = None) -> None:
    """Reject an item unless its source and deadline are verifiably admissible."""
    source = _registry().get(source_id)
    if not source:
        raise ValueError("Unknown source id")
    parsed = urlparse(source_url)
    official_host = urlparse(source["url"]).hostname
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname != official_host:
        raise ValueError("Candidate URL must use the registered official HTTPS host")
    if len(original_title.strip()) < 8:
        raise ValueError("Original title is too short to identify an opportunity")
    if deadline_at:
        try:
            deadline = datetime.fromisoformat(deadline_at.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("Deadline must be an ISO-8601 timestamp") from error
        if deadline.tzinfo is None:
            raise ValueError("Deadline must include a timezone")
        if deadline.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError("Expired opportunities cannot enter the queue")
