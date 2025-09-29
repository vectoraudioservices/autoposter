# scripts/db.py
import os, sqlite3, hashlib
from contextlib import contextmanager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "autoposter.db")

def _row_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = _row_factory
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
    finally:
        conn.close()

def init_db():
    with get_conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS jobs(
          id INTEGER PRIMARY KEY,
          client    TEXT NOT NULL,
          path      TEXT NOT NULL,
          caption   TEXT NOT NULL,
          eta       TEXT NOT NULL, -- UTC ISO8601
          status    TEXT NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','in_progress','done','failed')),
          posted_at TEXT,
          attempts  INTEGER DEFAULT 0,
          last_error TEXT,
          job_key   TEXT UNIQUE
        );""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_due ON jobs(status, eta);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_client ON jobs(client);")

def _job_key(client, path, eta_iso_utc):
    raw = f"{client}|{os.path.abspath(path)}|{eta_iso_utc}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()

def add_job(client, path, caption, eta_iso_utc):
    init_db()
    key = _job_key(client, path, eta_iso_utc)
    with get_conn() as c:
        c.execute("""
            INSERT OR IGNORE INTO jobs(client,path,caption,eta,status,job_key)
            VALUES (?,?,?,?, 'queued', ?)
        """, (client, os.path.abspath(path), caption, eta_iso_utc, key))
        row = c.execute("SELECT id FROM jobs WHERE job_key=?", (key,)).fetchone()
        return row["id"]

def upsert_client(client_name: str):
    # placeholder for future clients table; ensures DB ready
    init_db()

def get_due_jobs(limit=50):
    init_db()
    with get_conn() as c:
        return c.execute("""
            SELECT * FROM jobs
            WHERE status='queued' AND eta <= datetime('now')
            ORDER BY eta ASC
            LIMIT ?
        """, (limit,)).fetchall()

def mark_in_progress(job_id: int):
    with get_conn() as c:
        c.execute("UPDATE jobs SET status='in_progress', attempts=attempts+1 WHERE id=?", (job_id,))

def mark_done(job_id: int):
    with get_conn() as c:
        c.execute("UPDATE jobs SET status='done', posted_at=datetime('now') WHERE id=?", (job_id,))

def reschedule(job_id: int, new_eta_iso_utc: str, error_msg: str | None=None, set_failed: bool=False):
    with get_conn() as c:
        if set_failed:
            c.execute("UPDATE jobs SET status='failed', last_error=? WHERE id=?", (error_msg or "", job_id))
        else:
            c.execute("UPDATE jobs SET status='queued', eta=?, last_error=? WHERE id=?", (new_eta_iso_utc, error_msg or "", job_id))

def list_queue(limit=200):
    init_db()
    with get_conn() as c:
        return c.execute("""
            SELECT * FROM jobs
            WHERE status='queued'
            ORDER BY eta ASC
            LIMIT ?
        """,(limit,)).fetchall()

def clear_queue():
    with get_conn() as c:
        c.execute("DELETE FROM jobs WHERE status='queued';")
