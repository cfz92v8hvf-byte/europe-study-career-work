#!/usr/bin/env python3
"""Cloud-safe heartbeat: validate configuration, expire stale queue, regenerate dashboard."""
from __future__ import annotations
import json
from pathlib import Path
from dashboard import main as build_dashboard
from queue_store import connect, expire_stale
from operations_log import record

ROOT = Path(__file__).resolve().parents[1]
settings = json.loads((ROOT / "config" / "settings.json").read_text())
if settings["mode"] not in {"disabled", "review"}: raise RuntimeError("Cloud check refuses auto publication")
expired = expire_stale(connect(), settings["pending_expiry_hours"])
build_dashboard()
record("cloud_check", "ok", expired=str(expired), mode=settings["mode"])
print(f"OK: dashboard regenerated; expired={expired}; mode={settings['mode']}")
