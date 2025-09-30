
from __future__ import annotations
import sqlite3, json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "autoposter.db"

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def init_db():
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
          id           INTEGER PRIMARY KEY AUTOINCREMENT,
          client       TEXT NOT NULL,
          path         TEXT NOT NULL,
          content_type TEXT NOT NULL,
          caption      TEXT,
          eta          TEXT NOT NULL,
          status       TEXT NOT NULL DEFAULT 'queued',
          created_at   TEXT NOT NULL,
          posted_at    TEXT,
          extras       TEXT
        )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_jobs_client ON jobs(client)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_jobs_eta ON jobs(eta)")
        # HARD DEDUPE: one row per (client, path)
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_jobs_client_path ON jobs(client, path)")
        c.commit()

def get_job_by_path(client: str, path: str):
    with _conn() as c:
        return c.execute("SELECT * FROM jobs WHERE client=? AND path=? LIMIT 1", (client, path)).fetchone()

def add_job(client: str, path: str, *, content_type: str, caption: str|None=None, eta: str|None=None, extras: dict|None=None) -> int:
    eta = eta or _now_iso()
    ex = json.dumps(extras or {}, ensure_ascii=False)
    with _conn() as c:
        cur = c.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO jobs (client, path, content_type, caption, eta, status, created_at, extras) "
            "VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)",
            (client, path, content_type, caption, eta, _now_iso(), ex)
        )
        row = c.execute("SELECT id FROM jobs WHERE client=? AND path=? LIMIT 1", (client, path)).fetchone()
        c.commit()
        return int(row["id"])

def get_due_jobs(limit: int = 50, client: str | None = None, now_iso: str | None = None):
    now_iso = now_iso or _now_iso()
    with _conn() as c:
        if client:
            return c.execute(
                "SELECT * FROM jobs WHERE status='queued' AND client=? AND (eta IS NULL OR eta <= ?) "
                "ORDER BY id ASC LIMIT ?",
                (client, now_iso, limit)
            ).fetchall()
        return c.execute(
            "SELECT * FROM jobs WHERE status='queued' AND (eta IS NULL OR eta <= ?) "
            "ORDER BY id ASC LIMIT ?",
            (now_iso, limit)
        ).fetchall()

def mark_in_progress(job_id: int):
    with _conn() as c:
        c.execute("UPDATE jobs SET status='in_progress' WHERE id=?", (job_id,))
        c.commit()

def mark_done(job_id: int):
    with _conn() as c:
        c.execute("UPDATE jobs SET status='done', posted_at=? WHERE id=?", (_now_iso(), job_id))
        c.commit()

def reschedule(job_id: int, new_eta: str, reason: str|None=None):
    with _conn() as c:
        if reason:
            row = c.execute("SELECT extras FROM jobs WHERE id=?", (job_id,)).fetchone()
            old = {}
            if row and row["extras"]:
                try: old = json.loads(row["extras"])
                except Exception: old = {}
            old["reschedule_reason"] = reason
            ex = json.dumps(old, ensure_ascii=False)
            c.execute("UPDATE jobs SET eta=?, status='queued', extras=? WHERE id=?", (new_eta, ex, job_id))
        else:
            c.execute("UPDATE jobs SET eta=?, status='queued' WHERE id=?", (new_eta, job_id))
        c.commit()
