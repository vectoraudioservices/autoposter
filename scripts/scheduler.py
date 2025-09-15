import os
import json
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config", "schedule.json")
LOGS = os.path.join(ROOT, "logs")
QUEUE = os.path.join(LOGS, "queue.txt")

os.makedirs(LOGS, exist_ok=True)

def _load_config():
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"timezone": "America/New_York", "best_times": {"default_hours_24": [11, 15, 19]}}

def _next_slot(now: datetime, hours: list[int]) -> datetime:
    today = now.replace(minute=0, second=0, microsecond=0)
    candidates = [today.replace(hour=h) for h in hours]
    for t in candidates:
        if t > now:
            return t
    return candidates[0] + timedelta(days=1)

def _infer_client_from_path(filepath: str) -> str:
    content_dir = os.path.join(ROOT, "content")
    try:
        rel = os.path.relpath(filepath, content_dir)
        parts = rel.split(os.sep)
        if len(parts) >= 2 and parts[0] not in (".", ""):
            return parts[0]
    except Exception:
        pass
    current_txt = os.path.join(ROOT, "config", "current_client.txt")
    try:
        with open(current_txt, "r", encoding="utf-8") as f:
            name = f.read().strip()
            return name or "VectorManagement"
    except Exception:
        return "VectorManagement"

def add_to_queue(filepath: str, caption: str, minutes_from_now: int = None) -> datetime:
    cfg = _load_config()
    hours = cfg.get("best_times", {}).get("default_hours_24", [11, 15, 19])
    now = datetime.now()

    if minutes_from_now is not None:
        eta = now + timedelta(minutes=minutes_from_now)
    else:
        eta = _next_slot(now, hours)

    client = _infer_client_from_path(filepath)
    abspath = os.path.abspath(filepath)

    # Escape newlines safely
    safe_caption = caption.replace(os.linesep, "\\n")

    line = f"{eta.isoformat()}|{abspath}|{safe_caption}|client={client}"
    with open(QUEUE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return eta







