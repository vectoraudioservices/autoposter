# scripts/force_eta_now.py
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

# Load scripts/db.py by absolute path (no package import needed)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "scripts" / "db.py"

spec = importlib.util.spec_from_file_location("db", DB_PATH)
db = importlib.util.module_from_spec(spec)
assert spec and spec.loader, "Failed to prepare db module spec"
spec.loader.exec_module(db)  # type: ignore[attr-defined]

def main(client: str = "Luchiano") -> None:
    conn = db._conn()
    now = db._now_iso()
    cur = conn.execute(
        """
        UPDATE jobs
        SET eta = ?, status = 'queued', error = NULL
        WHERE client = ? AND status = 'queued'
        """,
        (now, client),
    )
    conn.commit()
    print(f"Forced {cur.rowcount} queued jobs for {client} to eta={now}")

if __name__ == "__main__":
    client = sys.argv[1] if len(sys.argv) > 1 else "Luchiano"
    main(client)
