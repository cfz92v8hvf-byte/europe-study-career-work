"""Append-only, credential-free operational log for cloud and local runs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "data" / "operations.jsonl"


def record(event: str, result: str, **details: str) -> None:
    if result not in {"ok", "warning", "error"}:
        raise ValueError("Unsupported result")
    forbidden = ("token", "secret", "password", "key")
    if any(word in field.casefold() for field in details for word in forbidden):
        raise ValueError("Credentials must never enter the operation log")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    payload = {"at": datetime.now(timezone.utc).isoformat(), "event": event, "result": result, "details": details}
    with LOG.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
