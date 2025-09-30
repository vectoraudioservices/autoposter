# scripts/queue_runner.py
from __future__ import annotations

import os
import argparse
import json
from typing import Dict, Any, Optional
from pathlib import Path
import importlib.util

# ----- Load db.py directly by path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "scripts" / "db.py"

spec = importlib.util.spec_from_file_location("db", DB_PATH)
db = importlib.util.module_from_spec(spec)
assert spec and spec.loader, "Failed to prepare db module spec"
spec.loader.exec_module(db)  # type: ignore[attr-defined]

CLIENTS_DIR = PROJECT_ROOT / "config" / "clients"

def load_client_config(client: str) -> Dict[str, Any]:
    p = CLIENTS_DIR / client / "client.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def today_quota_used(conn, client: str, content_type: str) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM jobs
        WHERE client = ? AND content_type = ? AND status = 'done'
          AND date(created_at) = date('now')
        """,
        (client, content_type),
    ).fetchone()
    return int((row or {"c": 0})["c"] or 0)

def should_throttle(conn, client: str, content_type: str, cfg: Dict[str, Any]) -> Optional[str]:
    if os.environ.get("IGNORE_QUOTA") == "1":
        return None
    max_per_day = (cfg.get("max_per_day") or {}).get(content_type)
    if not max_per_day:
        return None
    used = today_quota_used(conn, client, content_type)
    try:
        limit = int(max_per_day)
    except Exception:
        return None
    if used >= limit:
        return f"QUOTA REACHED {client}/{content_type} ({used}/{limit})"
    return None

def simulate_upload(kind: str, client: str, path: str, caption: str | None, dry_run: bool) -> bool:
    if dry_run:
        print(f"[DRY] Would upload {kind} for {client}: {path} (caption={caption!r})")
        return True
    print(f"[LIVE] Uploaded {kind} for {client}: {path}")
    return True

def _reschedule_one_hour(job_id: int) -> str:
    from datetime import datetime, timedelta, timezone
    new_eta = (datetime.now(timezone.utc) + timedelta(hours=1)).replace(microsecond=0).isoformat()
    db.reschedule(job_id, new_eta, reason="quota")
    return new_eta

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    conn = db._conn()
    cfg = load_client_config(args.client)
    ignore_quota = os.environ.get("IGNORE_QUOTA", "0")

    print(f"[runner] start (DRY_RUN={args.dry_run}) (IGNORE_QUOTA={ignore_quota})")

    jobs = db.get_due_jobs(limit=50, client=args.client)
    if not jobs:
        print("[runner] no due jobs")
        return

    for row in jobs:
        jid = row["id"]
        client = row["client"]
        kind = row["content_type"]
        path = row["path"]
        caption = row.get("caption")

        throttle = should_throttle(conn, client, kind, cfg)
        if throttle:
            new_eta = _reschedule_one_hour(jid)
            print(f"[runner] {throttle}. Rescheduled job#{jid} -> {new_eta}")
            if args.once:
                break
            continue

        db.mark_in_progress(jid)
        ok = simulate_upload(kind, client, path, caption, args.dry_run)
        if ok:
            db.mark_done(jid)
            print(f"[runner] job#{jid} done")
        else:
            db.reschedule(jid, db._now_iso(), reason="upload failed")
            print(f"[runner] job#{jid} failed -> rescheduled")

        if args.once:
            break

if __name__ == "__main__":
    main()
