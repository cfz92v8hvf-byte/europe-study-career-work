"""Apply narrow, traceable terminology corrections before the second audit."""
from __future__ import annotations


RULES = (
    ("phd candidate", "кандидат наук", "аспирант"),
    ("assistant professor", "доцент", "ассистент-профессор"),
)


def correct_review_titles(db) -> int:
    changed = 0
    for row in db.execute("SELECT id, original_title, title_ru FROM candidates WHERE status='review' AND title_ru IS NOT NULL"):
        title = row["title_ru"]
        revised = title
        original = row["original_title"].casefold()
        for source_term, wrong, right in RULES:
            if source_term in original:
                revised = revised.replace(wrong, right).replace(wrong.title(), right.title())
        if revised != title:
            db.execute("UPDATE candidates SET title_ru=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (revised, row["id"]))
            changed += 1
    db.commit()
    return changed
