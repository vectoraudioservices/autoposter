# scripts/queue_runner_demo.py
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

# ----- load scripts/db.py by absolute path (no package import required)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "scripts" / "db.py"

spec = importlib.util.spec_from_file_location("db", DB_PATH)
db = importlib.util.module_from_spec(spec)
assert spec and spec.loader, "Failed to prepare db module spec"
spec.loader.exec_module(db)  # type: ignore[attr-defined]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--dry-run", action="store_true", help="simulate upload; never post")
    ap.add_argument("--once", action="store_true", help="process at most one job (default)")
    args = ap.parse_args()

    print(f"[demo-runner] start (DRY_RUN={args.dry_run}) (quota=IGNORED)")

    jobs = db.get_due_jobs(limit=50, client=args.client)
    if not jobs:
        print("[demo-runner] no due jobs")
        return

    row = jobs[0]
    job_id = row["id"]
    client = row["client"]
    kind = row["content_type"]
    path = row["path"]
    caption = row.get("caption")

    db.mark_in_progress(job_id)

    if args.dry_run:
        print(f"[demo-runner] [DRY] Would upload {kind} for {client}: {path} (caption={caption!r})")
        db.mark_done(job_id)
        print(f"[demo-runner] job#{job_id} done (DRY)")
    else:
        db.mark_done(job_id)
        print(f"[demo-runner] job#{job_id} done (LIVE placeholder)")

    print("[demo-runner] exit")

if __name__ == "__main__":
    main()
