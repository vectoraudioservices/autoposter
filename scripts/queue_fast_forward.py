import os
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "logs", "queue.txt")

def main():
    if not os.path.exists(QUEUE):
        print("queue.txt is empty. Nothing to fast-forward.")
        return
    with open(QUEUE, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    if not lines:
        print("queue.txt is empty. Nothing to fast-forward.")
        return

    now = datetime.now().replace(microsecond=0) + timedelta(seconds=5)
    new_lines = []
    for ln in lines:
        parts = ln.split("|", 2)
        if len(parts) < 3:
            continue
        parts[0] = now.isoformat()
        new_lines.append("|".join(parts))

    with open(QUEUE, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")

    print(f"Fast-forwarded {len(new_lines)} queued item(s) to {now.isoformat()}")

if __name__ == "__main__":
    main()

