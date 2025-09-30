# C:\autoposter\scripts\list_jobs.py
from __future__ import annotations
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "autoposter.db"

def main():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    try:
        rows = con.execute("SELECT id,client,content_type,status,eta,path FROM jobs ORDER BY id ASC LIMIT 100").fetchall()
        for r in rows:
            print(f"#{r['id']} {r['client']}/{r['content_type']} {r['status']} eta={r['eta']} file={Path(r['path']).name}")
    finally:
        con.close()

if __name__ == "__main__":
    main()
