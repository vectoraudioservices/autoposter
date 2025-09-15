import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(ROOT, "logs")
QUEUE = os.path.join(LOGS, "queue.txt")
BACKUP = os.path.join(LOGS, "queue.reset.backup.txt")

def main():
    os.makedirs(LOGS, exist_ok=True)
    if os.path.exists(QUEUE) and os.path.getsize(QUEUE) > 0:
        shutil.copyfile(QUEUE, BACKUP)
        print(f"Backed up old queue to: {BACKUP}")
    open(QUEUE, "w", encoding="utf-8").close()
    print("Cleared queue.txt")

if __name__ == "__main__":
    main()
