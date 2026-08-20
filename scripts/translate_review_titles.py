#!/usr/bin/env python3
"""Translate review-queue titles without granting any publication capability."""
from __future__ import annotations

import argparse
import sqlite3
from typing import Callable

from mymemory_translator import translate_en_title_to_russian
from queue_store import connect


def pending_titles(db: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    if limit < 1 or limit > 12:
        raise ValueError("Translation limit must be between 1 and 12")
    return list(db.execute("""SELECT id, original_title FROM candidates
        WHERE status='review' AND (title_ru IS NULL OR trim(title_ru)='')
        ORDER BY discovered_at ASC LIMIT ?""", (limit,)))


def translate_pending(db: sqlite3.Connection, *, limit: int = 3,
                      translator: Callable[[sqlite3.Connection, str], str] = translate_en_title_to_russian) -> int:
    translated = 0
    for candidate in pending_titles(db, limit):
        title_ru = translator(db, candidate["original_title"])
        db.execute("UPDATE candidates SET title_ru=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (title_ru, candidate["id"]))
        db.commit()
        translated += 1
    return translated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="perform translation; default is dry listing")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    db = connect()
    candidates = pending_titles(db, args.limit)
    if not args.apply:
        print(f"DRY RUN: {len(candidates)} review titles await translation; no provider request was made.")
        return 0
    print(f"Translated review titles: {translate_pending(db, limit=args.limit)}; Telegram publication remains unavailable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
