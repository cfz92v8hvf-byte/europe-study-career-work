"""Independent, fail-closed queue for the Europe channel."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from candidate_validation import validate_candidate

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "queue.sqlite3"
ALLOWED = {"review", "approved", "scheduled", "published", "expired", "rejected"}


def review_capacity() -> int:
    settings = json.loads((ROOT / "config" / "settings.json").read_text(encoding="utf-8"))
    capacity = settings.get("max_review_candidates")
    if not isinstance(capacity, int) or capacity < 1:
        raise ValueError("max_review_candidates must be a positive integer")
    return capacity


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY,
        fingerprint TEXT NOT NULL UNIQUE,
        source_id TEXT NOT NULL,
        source_url TEXT NOT NULL UNIQUE,
        original_title TEXT NOT NULL,
        title_ru TEXT,
        original_summary TEXT,
        summary_ru TEXT,
        deadline_at TEXT,
        discovered_at TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('review','approved','scheduled','published','expired','rejected')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    existing = {row[1] for row in db.execute("PRAGMA table_info(candidates)")}
    for name in ("original_summary", "summary_ru"):
        if name not in existing:
            db.execute(f"ALTER TABLE candidates ADD COLUMN {name} TEXT")
    db.commit()
    return db


def fingerprint(source_url: str) -> str:
    return hashlib.sha256(source_url.strip().encode("utf-8")).hexdigest()


def add_candidate(db: sqlite3.Connection, *, source_id: str, source_url: str, original_title: str,
                  title_ru: str | None = None, original_summary: str | None = None,
                  summary_ru: str | None = None, deadline_at: str | None = None) -> bool:
    validate_candidate(source_id=source_id, source_url=source_url,
                       original_title=original_title, title_ru=title_ru, deadline_at=deadline_at)
    if db.execute("SELECT 1 FROM candidates WHERE source_url=?", (source_url,)).fetchone():
        return False
    pending = db.execute("SELECT COUNT(*) FROM candidates WHERE status='review'").fetchone()[0]
    if pending >= review_capacity():
        raise RuntimeError("Review queue is full; no additional candidates may be collected")
    now = datetime.now(timezone.utc).isoformat()
    try:
        db.execute("""INSERT INTO candidates
            (fingerprint, source_id, source_url, original_title, title_ru, original_summary, summary_ru, deadline_at, discovered_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'review')""",
            (fingerprint(source_url), source_id, source_url, original_title.strip(), title_ru,
             original_summary.strip() if original_summary else None, summary_ru.strip() if summary_ru else None,
             deadline_at, now))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def expire_stale(db: sqlite3.Connection, hours: int) -> int:
    threshold = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    result = db.execute("""UPDATE candidates SET status='expired', updated_at=CURRENT_TIMESTAMP
        WHERE status IN ('review', 'approved') AND discovered_at < ?""", (threshold,))
    db.commit()
    return result.rowcount


def transition(db: sqlite3.Connection, candidate_id: int, to_status: str) -> None:
    if to_status not in ALLOWED or to_status == "published":
        raise ValueError("Publishing is deliberately unavailable in this local queue layer")
    result = db.execute("UPDATE candidates SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (to_status, candidate_id))
    if result.rowcount != 1:
        raise KeyError(candidate_id)
    db.commit()
