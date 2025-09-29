# scripts/scheduler.py
from __future__ import annotations
import os, json, importlib.util
from datetime import datetime
from typing import Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT, "config", "schedule.json")
CONTENT_DIR = os.path.join(ROOT, "content")

def _load_mod(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod

# Load our local helpers/modules without relying on package imports
_db = _load_mod("db", os.path.join(ROOT, "scripts", "db.py"))
_tz = _load_mod("scheduler_tz", os.path.join(ROOT, "scripts", "scheduler_tz.py"))
next_local_slot = _tz.next_local_slot
to_local = _tz.to_local

DEFAULT_HOURS = [11, 15, 19]  # local hours (America/New_York)

def _read_config() -> dict:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _infer_client_and_type(abs_path: str) -> Tuple[str, str]:
    """
    Map content\<Client>\<feed|stories|reels|weekly>\file to (client, ctype).
    Fallback: ('VectorManagement', 'feed')
    """
    rel = os.path.relpath(abs_path, CONTENT_DIR)
    parts = rel.split(os.sep)
    client = "VectorManagement"
    ctype = "feed"
    if len(parts) >= 2:
        client = parts[0] or client
        c = (parts[1] or "").lower()
        if c in ("feed", "stories", "reels", "weekly"):
            ctype = c
    return client, ctype

def _hours_for_type(cfg: dict, ctype: str) -> list[int]:
    bt = (cfg.get("best_times") or {})
    if ctype == "reels":
        return bt.get("reels_hours_24") or bt.get("default_hours_24") or DEFAULT_HOURS
    if ctype == "stories":
        return bt.get("stories_hours_24") or bt.get("default_hours_24") or DEFAULT_HOURS
    if ctype == "weekly":
        return bt.get("weekly_hours_24") or bt.get("default_hours_24") or DEFAULT_HOURS
    return bt.get("default_hours_24") or DEFAULT_HOURS

def add_to_queue(path: str, caption: str) -> datetime:
    """
    Enqueue a job at the next time slot for its content type.
    Returns the ETA as a local datetime (for display); stores UTC in DB.
    """
    abs_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    cfg = _read_config()
    client, ctype = _infer_client_and_type(abs_path)
    hours = _hours_for_type(cfg, ctype)

    # compute UTC ETA and store
    eta_utc = next_local_slot(hours)  # returns aware UTC datetime
    eta_iso_utc = eta_utc.isoformat()

    _db.init_db()
    _db.add_job(client, abs_path, caption, eta_iso_utc)

    # return local time for logs
    return to_local(eta_utc)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scripts/scheduler.py <path-to-file> [caption]")
        raise SystemExit(1)
    p = sys.argv[1]
    cap = sys.argv[2] if len(sys.argv) >= 3 else "Test"
    eta = add_to_queue(p, cap)
    print("Queued:", p, "| ETA local:", eta.strftime("%Y-%m-%d %H:%M"))







