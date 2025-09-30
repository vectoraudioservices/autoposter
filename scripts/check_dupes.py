from __future__ import annotations
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "autoposter.db"

def main():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    try:
        rows = con.execute("""
            SELECT client, path, COUNT(*) AS cnt
            FROM jobs
            GROUP BY client, path
            HAVING COUNT(*) > 1
        """).fetchall()
        if not rows:
            print("✅ No duplicates by (client, path).")
        else:
            for r in rows:
                print("DUP:", r["client"], r["path"], "cnt=", r["cnt"])
    finally:
        con.close()

if __name__ == "__main__":
    main()
