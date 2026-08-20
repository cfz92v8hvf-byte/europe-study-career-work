#!/usr/bin/env python3
"""Fail closed until Google Cloud Translation is deliberately configured."""
from __future__ import annotations

import os


def main() -> int:
    if not os.getenv("GOOGLE_TRANSLATE_API_KEY"):
        raise RuntimeError("Translation preflight blocked: GOOGLE_TRANSLATE_API_KEY is not configured")
    print("OK: Google Translation credential is configured; no translation was requested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
