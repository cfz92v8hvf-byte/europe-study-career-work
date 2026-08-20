#!/usr/bin/env python3
"""Generate a credential-free static queue dashboard."""
from __future__ import annotations
import html
from pathlib import Path
from queue_store import connect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "index.html"

def main() -> None:
    db = connect()
    rows = db.execute("SELECT status, count(*) AS total FROM candidates GROUP BY status").fetchall()
    counts = {row[0]: row[1] for row in rows}
    cards = "".join(f"<li><b>{html.escape(status)}</b>: {count}</li>" for status, count in sorted(counts.items())) or "<li>Очередь пуста</li>"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f"""<!doctype html><meta charset=utf-8><title>Европа | Контроль</title>
<style>body{{font:16px system-ui;max-width:720px;margin:48px auto;padding:0 20px;color:#10244a}}h1{{color:#1557a6}}.note{{padding:16px;background:#eef6ff;border-radius:12px}}</style>
<h1>Европа | Учёба • Карьера • Работа</h1><p class=note>Панель очереди. Автопубликация отключена до отдельной проверки.</p><h2>Статусы</h2><ul>{cards}</ul>""", encoding="utf-8")

if __name__ == "__main__": main()
