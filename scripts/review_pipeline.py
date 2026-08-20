#!/usr/bin/env python3
"""Cloud-safe official-source pipeline ending in the separate review queue."""
from __future__ import annotations

import json

from dashboard import main as build_dashboard
from euraxess_review import collect
from operations_log import record
from queue_store import connect, review_capacity
from review_queue_audit import audit
from translate_review_titles import translate_pending
from translate_review_summaries import translate_pending_summaries


def run(*, max_collect: int = 3, collector=collect, translator=translate_pending, db=None) -> dict[str, int]:
    """Collect only available review slots, translate titles, and stop before publishing."""
    if max_collect < 1 or max_collect > 3:
        raise ValueError("max_collect must be between 1 and 3")
    owns_db = db is None
    db = db or connect()
    try:
        review_count = db.execute("SELECT COUNT(*) FROM candidates WHERE status='review'").fetchone()[0]
        slots = max(0, review_capacity() - review_count)
        collected_rows = collector(min(max_collect, slots), enqueue=True) if slots else []
        added = sum(1 for row in collected_rows if row.get("added_to_review") is True)
        translated = translator(db, limit=min(max_collect, slots)) if slots else 0
        summaries_translated = translate_pending_summaries(db, limit=min(max_collect, slots)) if slots else 0
        audited = audit(db)
        result = {"review_slots": slots, "collected": added, "translated": translated, "summaries_translated": summaries_translated, "audited": audited}
        record("review_pipeline", "ok", **{key: str(value) for key, value in result.items()})
        return result
    finally:
        if owns_db:
            db.close()


def main() -> int:
    result = run()
    build_dashboard()
    print(json.dumps({**result, "publication": "blocked"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
