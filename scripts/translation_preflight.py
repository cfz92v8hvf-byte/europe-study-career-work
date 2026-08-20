#!/usr/bin/env python3
"""Readiness check for the isolated, keyless MyMemory review translator."""
from __future__ import annotations

from mymemory_translator import SAFE_DAILY_CAP


def main() -> int:
    if SAFE_DAILY_CAP != 4_000:
        raise RuntimeError("Translation preflight blocked: unexpected free-usage safety cap")
    print("OK: isolated MyMemory review translator is ready; no translation was requested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
