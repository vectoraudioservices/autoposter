import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(ROOT, "logs")
QUEUE = os.path.join(LOGS, "queue.txt")
BACKUP = os.path.join(LOGS, "queue.hard_clean.backup.txt")

ISO_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}T")  # e.g., 2025-09-09T...

def main():
    os.makedirs(LOGS, exist_ok=True)
    if not os.path.exists(QUEUE):
        print("queue.txt not found; nothing to clean.")
        return

    with open(QUEUE, "r", encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh]

    # Backup before changes
    shutil.copyfile(QUEUE, BACKUP)

    kept = [ln for ln in lines if ln.strip() and ISO_PREFIX.match(ln)]
    with open(QUEUE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(kept) + ("\n" if kept else ""))

    print(f"Hard cleaned queue. Kept {len(kept)} line(s). Backup at {BACKUP}")

if __name__ == "__main__":
    main()
