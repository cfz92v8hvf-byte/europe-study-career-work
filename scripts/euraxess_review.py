#!/usr/bin/env python3
"""Collect official EURAXESS offers into review only; publishing is unavailable here."""
from __future__ import annotations

import argparse
import json

from euraxess_adapter import discover_offer_urls, fetch_offer_details, fetch_search_html
from queue_store import add_candidate, connect


def collect(limit: int, *, enqueue: bool = False) -> list[dict[str, str | bool | None]]:
    if limit < 1 or limit > 20:
        raise ValueError("limit must be between 1 and 20")
    urls = discover_offer_urls(fetch_search_html())[:limit]
    results: list[dict[str, str | bool | None]] = []
    db = connect() if enqueue else None
    try:
        for url in urls:
            try:
                title, summary = fetch_offer_details(url)
            except Exception as error:
                results.append({"source_url": url, "original_title": None, "added_to_review": None,
                                "error": f"official page unavailable: {type(error).__name__}"})
                continue
            added = add_candidate(
                db, source_id="euraxess-jobs", source_url=url, original_title=title, original_summary=summary
            ) if db else None
            results.append({"source_url": url, "original_title": title, "has_original_summary": bool(summary), "added_to_review": added})
    finally:
        if db:
            db.close()
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--enqueue", action="store_true", help="Add candidates only with review status")
    args = parser.parse_args()
    print(json.dumps(collect(args.limit, enqueue=args.enqueue), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
