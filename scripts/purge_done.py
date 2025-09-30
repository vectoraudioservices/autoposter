# C:\autoposter\scripts\purge_done.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "autoposter.db"

def main(days=30):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    con = sqlite3.connect(DB)
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM jobs WHERE status='done' AND posted_at IS NOT NULL AND posted_at < ?", (cutoff.isoformat(),))
        print(f"Deleted {cur.rowcount} old done rows (< {cutoff.isoformat()})")
        con.commit()
    finally:
        con.close()

if __name__ == "__main__":
    main()
