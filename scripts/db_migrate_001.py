# scripts/db_migrate_001.py
import os, sqlite3, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "autoposter.db")
os.makedirs(os.path.dirname(DB), exist_ok=True)

def table_cols(conn, table):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table});").fetchall()]

def ensure_jobs_exists(conn):
    # Create minimal table if it doesn't exist at all
    conn.execute("""
    CREATE TABLE IF NOT EXISTS jobs(
      id INTEGER PRIMARY KEY,
      client    TEXT NOT NULL,
      path      TEXT NOT NULL,
      caption   TEXT NOT NULL,
      eta       TEXT NOT NULL,
      status    TEXT NOT NULL DEFAULT 'queued'
    );
    """)

def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    ensure_jobs_exists(conn)
    cols = set(table_cols(conn, "jobs"))

    # If already migrated (job_key exists), stop
    if "job_key" in cols:
        print("DB already migrated (job_key present).")
        conn.close()
        return

    print("Migrating jobs table to add job_key + states + indexes...")

    # Build SELECT list safely based on existing columns
    sel_cols = ["id", "client", "path", "caption", "eta"]
    if "status" in cols:
        sel_cols.append("status")
    else:
        # some very old tables may not have status
        sel_cols.append("'queued' AS status")

    # optional columns (supply defaults if missing)
    if "posted_at" in cols:
        sel_cols.append("posted_at")
    else:
        sel_cols.append("NULL AS posted_at")

    if "attempts" in cols:
        sel_cols.append("attempts")
    else:
        sel_cols.append("0 AS attempts")

    if "last_error" in cols:
        sel_cols.append("last_error")
    else:
        sel_cols.append("NULL AS last_error")

    sel_sql = "SELECT " + ", ".join(sel_cols) + " FROM jobs"

    # Create new table with the hardened schema
    conn.execute("""
    CREATE TABLE IF NOT EXISTS jobs_new(
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
    );
    """)

    # Copy rows, compute job_key = sha1(client|abs(path)|eta)
    rows = conn.execute(sel_sql).fetchall()
    ins = conn.execute
    for r in rows:
        client = r["client"]
        path_abs = os.path.abspath(r["path"])
        eta = r["eta"]
        status = r["status"] if r["status"] else "queued"
        posted_at = r["posted_at"]
        attempts = r["attempts"] if r["attempts"] is not None else 0
        last_error = r["last_error"]

        raw = f"{client}|{path_abs}|{eta}".encode("utf-8")
        key = hashlib.sha1(raw).hexdigest()

        ins("""
            INSERT OR IGNORE INTO jobs_new
            (id, client, path, caption, eta, status, posted_at, attempts, last_error, job_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (r["id"], client, path_abs, r["caption"], eta, status, posted_at, attempts, last_error, key))

    # Replace table atomically
    conn.execute("DROP TABLE jobs;")
    conn.execute("ALTER TABLE jobs_new RENAME TO jobs;")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_due ON jobs(status, eta);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_client ON jobs(client);")
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    main()


