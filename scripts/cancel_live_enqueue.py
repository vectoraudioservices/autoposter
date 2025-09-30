# scripts/cancel_live_enqueue.py
from __future__ import annotations

import importlib.util
from pathlib import Path

# Load db.py directly by path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "scripts" / "db.py"
spec = importlib.util.spec_from_file_location("db", DB_PATH)
db = importlib.util.module_from_spec(spec)
assert spec and spec.loader, "Failed to prepare db module spec"
spec.loader.exec_module(db)  # type: ignore[attr-defined]

CLIENT = "Luchiano"
LIVE_PATH = r"C:\content\Luchiano\feed\live_demo.jpg"

def main() -> None:
    conn = db._conn()
    # Push ETA far into the future so it won't be picked up accidentally
    FUTURE = "2100-01-01T00:00:00+00:00"

    rows = conn.execute(
        """
        SELECT id, status, eta
        FROM jobs
        WHERE client = ? AND path = ?
        ORDER BY id DESC
        """,
        (CLIENT, LIVE_PATH),
    ).fetchall() or []

    if not rows:
        print("[cancel-live] No jobs found for live_demo.jpg — nothing to cancel.")
        return

    changed = 0
    for r in rows:
        jid = int(r["id"])
        # Only adjust jobs that aren't already marked done
        if r["status"] != "done":
            conn.execute(
                "UPDATE jobs SET status='queued', eta=? WHERE id=?",
                (FUTURE, jid),
            )
            changed += 1

    conn.commit()
    print(f"[cancel-live] Adjusted {changed} job(s) for path={LIVE_PATH} -> status=queued, eta={FUTURE}")

if __name__ == "__main__":
    main()
