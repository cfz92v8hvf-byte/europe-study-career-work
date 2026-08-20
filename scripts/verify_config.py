#!/usr/bin/env python3
"""Fail-closed verifier for the independent channel configuration."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    settings = load("config/settings.json")
    registry = load("config/sources.json")
    assert settings["project"] == "europe-study-career-work"
    assert settings["mode"] in {"disabled", "review"}, "Automatic publication is not allowed"
    assert registry["policy"] == "official-only"
    ids: set[str] = set()
    for source in registry["sources"]:
        assert source["id"] not in ids
        ids.add(source["id"])
        parsed = urlparse(source["url"])
        assert parsed.scheme == "https" and parsed.netloc
        if source["enabled"]:
            assert source["id"] == "euraxess-jobs", "Only the tested EURAXESS review adapter may collect"
            assert source["collection"] == "scheduled_review_adapter"
        else:
            assert source["collection"] == "manual_adapter_required"
    print(f"OK: {len(ids)} official sources are registered; publication is blocked and review automation is controlled.")


if __name__ == "__main__":
    main()
