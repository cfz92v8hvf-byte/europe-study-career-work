#!/usr/bin/env python3
"""Revalidate every review card after translation and before it can be seen downstream."""
from __future__ import annotations

from candidate_validation import validate_candidate


def audit(db) -> int:
    rows = list(db.execute("""SELECT source_id, source_url, original_title, title_ru, summary_ru, deadline_at
        FROM candidates WHERE status='review' ORDER BY id"""))
    for row in rows:
        if not row["title_ru"]:
            raise RuntimeError("Review queue audit blocked: untranslated card detected")
        title = row["title_ru"].casefold()
        original = row["original_title"].casefold()
        if "phd candidate" in original and "кандидат наук" in title:
            raise RuntimeError("Review queue audit blocked: PhD Candidate requires an аспирант-style translation")
        if "assistant professor" in original and "доцент" in title:
            raise RuntimeError("Review queue audit blocked: Assistant Professor requires literal title review")
        summary = row["summary_ru"] or ""
        if summary and any(word in summary.casefold() for word in (" the ", " hereby ", " under the ")):
            raise RuntimeError("Review queue audit blocked: untranslated English fragment in summary")
        validate_candidate(
            source_id=row["source_id"], source_url=row["source_url"],
            original_title=row["original_title"], title_ru=row["title_ru"], deadline_at=row["deadline_at"],
        )
    return len(rows)
