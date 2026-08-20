#!/usr/bin/env python3
"""Verify bot identity and channel publishing rights without sending a post."""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def api(token: str, method: str, payload: dict | None = None) -> dict:
    request = Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode("utf-8") if payload else None,
        headers={"Content-Type": "application/json"} if payload else {},
        method="POST" if payload else "GET",
    )
    try:
        with urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as error:
        raise RuntimeError("Telegram preflight failed; no post was attempted") from error
    if not body.get("ok"):
        raise RuntimeError("Telegram preflight was rejected; no post was attempted")
    return body["result"]


def can_publish(member: dict) -> bool:
    return member.get("status") in {"administrator", "creator"} and member.get("can_post_messages", True)


def main() -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel = os.getenv("TELEGRAM_CHANNEL")
    if not token or not channel:
        raise RuntimeError("Preflight blocked: required Telegram configuration is absent")
    bot = api(token, "getMe")
    member = api(token, "getChatMember", {"chat_id": channel, "user_id": bot["id"]})
    if not can_publish(member):
        raise RuntimeError("Preflight blocked: bot is not a channel administrator with posting rights")
    print("OK: bot administrator rights verified; no post was sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
