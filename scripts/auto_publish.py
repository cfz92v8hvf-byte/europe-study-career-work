#!/usr/bin/env python3
"""Publish one quality-checked official card with a durable Telegram receipt."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from operations_log import record
from post_formatter import format_post
from queue_store import connect, mark_published
from review_queue_audit import audit
from telegram_preflight import main as preflight
from telegram_publish import send_message

ROOT = Path(__file__).resolve().parents[1]


def settings() -> dict:
    return json.loads((ROOT / "config" / "settings.json").read_text(encoding="utf-8"))


def bootstrap_manual_posts(db, urls: list[str]) -> int:
    """Record known manual posts once, so the bot can never repost their source URLs."""
    marked = 0
    for url in urls:
        row = db.execute("SELECT id, status FROM candidates WHERE source_url=?", (url,)).fetchone()
        if row and row["status"] != "published":
            mark_published(db, row["id"])
            marked += 1
    return marked


def can_publish_now(db, now: datetime, config: dict) -> bool:
    since_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today = db.execute("SELECT COUNT(*) FROM candidates WHERE status='published' AND published_at>=?", (since_day,)).fetchone()[0]
    if today >= int(config["max_posts_per_day"]):
        return False
    latest = db.execute("SELECT published_at FROM candidates WHERE status='published' AND published_at IS NOT NULL ORDER BY published_at DESC LIMIT 1").fetchone()
    if not latest:
        return True
    return now - datetime.fromisoformat(latest[0]) >= timedelta(hours=int(config["minimum_hours_between_posts"]))


def publish_one(*, sender=send_message, preflight_check=preflight, db=None, now=None) -> dict[str, int]:
    config = settings()
    if config.get("mode") != "auto":
        raise RuntimeError("Automatic publishing is disabled in settings")
    owns_db = db is None
    db = db or connect()
    now = now or datetime.now(timezone.utc)
    try:
        bootstrapped = bootstrap_manual_posts(db, config.get("bootstrap_published_urls", []))
        audit(db)
        if not can_publish_now(db, now, config):
            result = {"bootstrapped": bootstrapped, "published": 0}
            record("auto_publish", "ok", **{key: str(value) for key, value in result.items()})
            return result
        row = db.execute("""SELECT id, title_ru, summary_ru, source_url
            FROM candidates WHERE status='review' ORDER BY discovered_at ASC LIMIT 1""").fetchone()
        if not row:
            result = {"bootstrapped": bootstrapped, "published": 0}
            record("auto_publish", "ok", **{key: str(value) for key, value in result.items()})
            return result
        message = format_post(title_ru=row["title_ru"], summary_ru=row["summary_ru"],
                              source_name="Официальный источник EURAXESS", source_url=row["source_url"])
        preflight_check()
        message_id = sender(os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHANNEL"], message)
        mark_published(db, row["id"], message_id=message_id)
        result = {"bootstrapped": bootstrapped, "published": 1}
        record("auto_publish", "ok", message_id=str(message_id), **{key: str(value) for key, value in result.items()})
        return result
    finally:
        if owns_db:
            db.close()


def main() -> int:
    result = publish_one()
    print(f"OK: bootstrapped={result['bootstrapped']}; published={result['published']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
