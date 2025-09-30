# scripts/clean_demo_db.py
from __future__ import annotations

import json
import importlib.util
from pathlib import Path

# Load scripts/db.py by absolute path (no package import needed)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "scripts" / "db.py"

spec = importlib.util.spec_from_file_location("db", DB_PATH)
db = importlib.util.module_from_spec(spec)
assert spec and spec.loader, "Failed to prepare db module spec"
spec.loader.exec_module(db)  # type: ignore[attr-defined]

def main(client: str = "Luchiano") -> None:
    conn = db._conn()

    # Find rows that have a non-empty error field
    rows = conn.execute(
        """
        SELECT id, extras, error
        FROM jobs
        WHERE client = ? AND error IS NOT NULL AND error <> ''
        """,
        (client,),
    ).fetchall() or []

    if not rows:
        print(f"[clean] No error rows found for {client}. Nothing to do.")
        return

    fixed = 0
    for r in rows:
        jid = int(r["id"])
        extras_raw = r["extras"] or "{}"
        try:
            extras = json.loads(extras_raw)
        except Exception:
            extras = {"_raw": extras_raw}
        # Preserve the old error inside extras
        extras["error_note"] = r["error"]
        extras["source"] = "demo-clean"

        conn.execute(
            """
            UPDATE jobs
            SET status='done', error=NULL, extras=?
            WHERE id = ?
            """,
            (json.dumps(extras, ensure_ascii=False), jid),
        )
        fixed += 1

    conn.commit()
    print(f"[clean] Updated {fixed} row(s) for client={client} -> status=done, error cleared")

if __name__ == "__main__":
    main("Luchiano")
