import os, importlib.util

# Load db.py from the same folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "db.py")
if not os.path.exists(DB_FILE):
    raise SystemExit(f"db.py not found at: {DB_FILE}")

spec = importlib.util.spec_from_file_location("db", DB_FILE)
db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)  # type: ignore

def main():
    db.init_db()
    db.clear_queue()
    print("Cleared all queued (status=queued) jobs from DB.")

if __name__ == "__main__":
    main()
