"""Independent, fail-closed queue for the Europe channel."""
import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "queue.sqlite3"
ALLOWED = {"review", "approved", "scheduled", "published", "expired", "rejected"}

def connect(path=DB_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS candidates (id INTEGER PRIMARY KEY, fingerprint TEXT UNIQUE NOT NULL, source_url TEXT UNIQUE NOT NULL, status TEXT NOT NULL, discovered_at TEXT NOT NULL)")
    return db

def add_candidate(db, source_url):
    try:
        db.execute("INSERT INTO candidates VALUES (NULL, ?, ?, 'review', ?)", (hashlib.sha256(source_url.encode()).hexdigest(), source_url, datetime.now(timezone.utc).isoformat()))
        db.commit(); return True
    except sqlite3.IntegrityError:
        return False

def expire_stale(db, hours):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    result = db.execute("UPDATE candidates SET status='expired' WHERE status IN ('review','approved') AND discovered_at < ?", (cutoff,))
    db.commit(); return result.rowcount

def transition(db, candidate_id, status):
    if status not in ALLOWED or status == 'published':
        raise ValueError('Publishing is deliberately unavailable in this local queue layer')
    db.execute("UPDATE candidates SET status=? WHERE id=?", (status, candidate_id)); db.commit()
