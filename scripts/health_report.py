# C:\autoposter\scripts\health_report.py
from __future__ import annotations
import sqlite3, json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "autoposter.db"

def main():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    try:
        rows = con.execute("""
            SELECT client,
                   SUM(CASE WHEN status='queued' THEN 1 ELSE 0 END) as queued,
                   SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END) as in_progress,
                   SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) as done
            FROM jobs
            GROUP BY client
            ORDER BY client
        """).fetchall()
        print("=== Queue Summary ===")
        for r in rows:
            print(f"{r['client']}: queued={r['queued'] or 0}, in_progress={r['in_progress'] or 0}, done={r['done'] or 0}")

        print("\n=== Recent Activity (last 24h) ===")
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        rows = con.execute("SELECT id,client,content_type,status,posted_at,eta,path,extras FROM jobs WHERE posted_at>=? OR eta>=? ORDER BY id DESC LIMIT 50",
                           (since, since)).fetchall()
        for r in rows:
            ex = {}
            try:
                if r["extras"]: ex = json.loads(r["extras"])
            except Exception:
                pass
            reason = ex.get("reschedule_reason")
            print(f"#{r['id']} {r['client']}/{r['content_type']} {r['status']} eta={r['eta']} posted_at={r['posted_at']} file={Path(r['path']).name} reason={reason}")
    finally:
        con.close()

if __name__ == "__main__":
    main()
