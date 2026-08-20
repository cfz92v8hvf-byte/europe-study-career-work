#!/usr/bin/env python3
"""Fail closed until a dedicated translation credential is configured."""
from __future__ import annotations
import os
def main() -> int:
    if not os.getenv("TRANSLATION_API_KEY"):
        raise RuntimeError("Translation preflight blocked: TRANSLATION_API_KEY is not configured")
    print("OK: dedicated translation credential is configured; no translation was requested.")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
