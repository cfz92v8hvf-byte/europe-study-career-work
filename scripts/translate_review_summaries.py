"""Translate only short official descriptions in review cards; never publish."""
from __future__ import annotations

from mymemory_translator import translate_en_text_to_russian


def translate_pending_summaries(db, *, limit: int = 3, translator=translate_en_text_to_russian) -> int:
    rows = list(db.execute("""SELECT id, original_summary FROM candidates
        WHERE status='review' AND original_summary IS NOT NULL
        AND (summary_ru IS NULL OR trim(summary_ru)='') ORDER BY discovered_at LIMIT ?""", (limit,)))
    completed = 0
    for row in rows:
        translated = translator(db, row["original_summary"])
        if len(translated) < 20:
            raise ValueError("Translated official description is too short")
        db.execute("UPDATE candidates SET summary_ru=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (translated, row["id"]))
        db.commit()
        completed += 1
    return completed
