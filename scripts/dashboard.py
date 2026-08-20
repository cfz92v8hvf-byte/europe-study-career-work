#!/usr/bin/env python3
"""Generate a credential-free static queue dashboard."""
from __future__ import annotations
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from mymemory_translator import SAFE_DAILY_CAP, used_today
from queue_store import connect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "index.html"
SOURCE_HEALTH = ROOT / "docs" / "source-health.json"

def main() -> None:
    db = connect()
    rows = db.execute("SELECT status, count(*) AS total FROM candidates GROUP BY status").fetchall()
    counts = {row[0]: row[1] for row in rows}
    translated_today = used_today(db)
    translation_note = (f"MyMemory: {translated_today} из {SAFE_DAILY_CAP} символов сегодня. "
                        "Перевод работает только для карточек review; публикация недоступна.")
    cards = "".join(f"<li><b>{html.escape(status)}</b>: {count}</li>" for status, count in sorted(counts.items())) or "<li>Очередь пуста</li>"
    source_note = "Источник EURAXESS ещё не проверялся."
    if SOURCE_HEALTH.exists():
        health = json.loads(SOURCE_HEALTH.read_text(encoding="utf-8"))
        source_note = (f"EURAXESS: проверено карточек — {health['offers_checked']}; "
                       f"ошибок — {health['failures']}; UTC — {html.escape(health['checked_at'])}.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f"""<!doctype html><meta charset=utf-8><title>Европа | Контроль</title>
<style>body{{font:16px system-ui;max-width:720px;margin:48px auto;padding:0 20px;color:#10244a}}h1{{color:#1557a6}}.note{{padding:16px;background:#eef6ff;border-radius:12px}}</style>
<h1>Европа | Учёба • Карьера • Работа</h1><p class=note>Панель очереди. Автопубликация отключена до отдельной проверки.</p><h2>Статусы</h2><ul>{cards}</ul><h2>Перевод</h2><p>{translation_note}</p><h2>Официальные источники</h2><p>{source_note}</p><p>Обновлено (UTC): {datetime.now(timezone.utc).isoformat()}</p>""", encoding="utf-8")

if __name__ == "__main__": main()
