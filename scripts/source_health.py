#!/usr/bin/env python3
"""Record credential-free health data for official source discovery."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from euraxess_review import collect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "source-health.json"


def main() -> None:
    rows = collect(3)
    failures = sum(1 for row in rows if row.get("error"))
    data = {
        "source": "euraxess-jobs",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "offers_checked": len(rows),
        "failures": failures,
        "mode": "review-only",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    main()
