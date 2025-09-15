import os
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(ROOT, "logs")
QUEUE = os.path.join(LOGS, "queue.txt")
BACKUP = os.path.join(LOGS, "queue.before_clean.backup.txt")

def parse_ok(line: str) -> bool:
    try:
        parts = line.split("|", 3)
        if len(parts) < 3:
            return False
        datetime.fromisoformat(parts[0])  # raises if bad
        # parts[1] path can be anything
        # parts[2] caption (escaped \n ok)
        # optional parts[3] like "client=Name"
        return True
    except Exception:
        return False

def main():
    if not os.path.exists(QUEUE):
        print("queue.txt not found; nothing to clean.")
        return
    with open(QUEUE, "r", encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh if ln.strip()]

    if not lines:
        print("queue.txt already empty.")
        return

    # backup
    shutil.copyfile(QUEUE, BACKUP)

    good = [ln for ln in lines if parse_ok(ln)]
    with open(QUEUE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(good) + ("\n" if good else ""))

    print(f"Cleaned queue. Kept {len(good)} valid line(s). Backup at {BACKUP}")

if __name__ == "__main__":
    main()

