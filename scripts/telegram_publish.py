#!/usr/bin/env python3
"""Fail-closed Telegram test publisher for the isolated Europe channel."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from operations_log import record


def test_message() -> str:
    return (
        "🧪 Тест автоматизации канала «Европа | Учёба • Карьера • Работа»\n\n"
        "Это служебная проверка отдельного контура публикации. "
        "Пост не содержит вакансий и не запускает регулярную публикацию.\n\n"
        "#тест_автоматизации"
    )


def send_message(token: str, channel: str, message: str) -> int:
    payload = json.dumps({"chat_id": channel, "text": message, "parse_mode": "HTML", "disable_web_page_preview": False}).encode("utf-8")
    request = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as error:
        raise RuntimeError("Telegram test delivery failed; no retry is attempted") from error
    if not result.get("ok") or not isinstance(result.get("result", {}).get("message_id"), int):
        raise RuntimeError("Telegram did not confirm a message id")
    return result["result"]["message_id"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--send-test", action="store_true", help="Send one explicitly authorised test post")
    args = parser.parse_args()
    if not args.send_test:
        print("DRY RUN: Telegram test post is blocked until --send-test is supplied.")
        return 0
    if os.getenv("ENABLE_TELEGRAM_TEST") != "YES":
        raise RuntimeError("Test delivery blocked: ENABLE_TELEGRAM_TEST must equal YES")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel = os.getenv("TELEGRAM_CHANNEL")
    if not token or not channel:
        raise RuntimeError("Test delivery blocked: required Telegram configuration is absent")
    message_id = send_message(token, channel, test_message())
    record("telegram_test", "ok", channel=channel, message_id=str(message_id), at=datetime.now(timezone.utc).isoformat())
    print(f"OK: Telegram confirmed test message id {message_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
