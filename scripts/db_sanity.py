import os, importlib.util

# Locate db.py next to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "db.py")
if not os.path.exists(DB_FILE):
    raise SystemExit(f"db.py not found at: {DB_FILE}")

# Dynamically load db.py as module "db"
spec = importlib.util.spec_from_file_location("db", DB_FILE)
db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)  # type: ignore

def main():
    db.init_db()
    print(f"DB ready at: {db.DB_PATH}")
    exists = os.path.exists(db.DB_PATH)
    size = os.path.getsize(db.DB_PATH) if exists else 0
    print(f"Exists: {exists}  |  Size: {size} bytes")

if __name__ == "__main__":
    main()



