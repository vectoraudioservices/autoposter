import os, sys, argparse, importlib.util
from datetime import datetime, timedelta

# Load db.py from the same folder (no package import needed)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "db.py")
if not os.path.exists(DB_FILE):
    raise SystemExit(f"db.py not found at: {DB_FILE}")

spec = importlib.util.spec_from_file_location("db", DB_FILE)
db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)  # type: ignore

def main():
    ap = argparse.ArgumentParser(description="Fast-forward all queued DB jobs to run soon.")
    ap.add_argument("--seconds", type=int, default=10, help="How many seconds from now to schedule (default: 10)")
    args = ap.parse_args()

    db.init_db()
    now = datetime.now()
    new_eta = (now + timedelta(seconds=max(1, args.seconds))).isoformat()

    # Fetch queued items (any ETA), then set new ETA
    with db.get_conn() as c:
        rows = c.execute("SELECT id, client, path, eta FROM jobs WHERE status='queued' ORDER BY eta ASC").fetchall()
        for r in rows:
            c.execute("UPDATE jobs SET eta=? WHERE id=?", (new_eta, r["id"]))

    print(f"Fast-forwarded {len(rows)} queued item(s) to {new_eta}")

if __name__ == "__main__":
    main()


