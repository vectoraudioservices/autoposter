from __future__ import annotations
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "autoposter.db"

def main():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    try:
        dups = con.execute("""
            SELECT client, path, MIN(id) AS keep_id, COUNT(*) AS cnt
            FROM jobs
            GROUP BY client, path
            HAVING COUNT(*) > 1
        """).fetchall()
        total = 0
        for r in dups:
            client, path, keep_id = r["client"], r["path"], r["keep_id"]
            cur = con.execute(
                "DELETE FROM jobs WHERE client=? AND path=? AND id<>?",
                (client, path, keep_id)
            )
            total += cur.rowcount
            print(f"Cleaned {client} {Path(path).name}: kept id={keep_id}, removed={cur.rowcount}")
        con.commit()
        # Rebuild unique index just in case
        con.execute("DROP INDEX IF EXISTS ux_jobs_client_path")
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_jobs_client_path ON jobs(client, path)")
        con.commit()
        print(f"Done. Removed {total} duplicate rows and ensured unique index.")
    finally:
        con.close()

if __name__ == "__main__":
    main()
