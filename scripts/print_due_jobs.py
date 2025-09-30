# scripts/print_due_jobs.py
from __future__ import annotations

import importlib.util
from pathlib import Path

# Load scripts/db.py by file path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "scripts" / "db.py"

spec = importlib.util.spec_from_file_location("db", DB_PATH)
db = importlib.util.module_from_spec(spec)
assert spec and spec.loader, "Failed to prepare db module spec"
spec.loader.exec_module(db)  # type: ignore[attr-defined]

def main(client: str = "Luchiano") -> None:
    now = db._now_iso()
    print(f"NOW: {now}")
    jobs = db.get_due_jobs(limit=50, client=client, now_iso=now)
    if not jobs:
        print("NO DUE JOBS")
        conn = db._conn()
        rows = conn.execute(
            """
            SELECT id, client, content_type, status, eta, created_at, path
            FROM jobs
            WHERE client = ? AND status = 'queued'
            ORDER BY id DESC
            LIMIT 10
            """,
            (client,),
        ).fetchall()
        print("\nLATEST QUEUED (debug):")
        for r in rows or []:
            print(f"  id={r['id']} type={r['content_type']} status={r['status']} eta={r['eta']} path={r['path']}")
        return

    print("DUE JOBS:")
    for r in jobs:
        print(f"  id={r['id']} type={r['content_type']} eta={r['eta']} status={r['status']} path={r['path']}")

if __name__ == "__main__":
    main("Luchiano")
