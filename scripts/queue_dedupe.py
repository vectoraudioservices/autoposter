import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "logs", "queue.txt")
BACKUP = os.path.join(ROOT, "logs", "queue.backup.txt")

def parse(line: str):
    try:
        when_str, path, caption = line.split("|", 2)
        return datetime.fromisoformat(when_str), path, caption
    except Exception:
        return None, None, None

def main():
    if not os.path.exists(QUEUE):
        print("No queue.txt found.")
        return

    with open(QUEUE, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    if not lines:
        print("Queue is empty.")
        return

    # backup first (safety)
    with open(BACKUP, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    best_by_path = {}
    for ln in lines:
        when, path, caption = parse(ln)
        if when is None or not path:
            continue
        keep = best_by_path.get(path)
        if keep is None or when < keep[0]:
            best_by_path[path] = (when, path, caption)

    deduped = [
        f"{when.isoformat()}|{path}|{caption}"
        for (when, path, caption) in sorted(best_by_path.values(), key=lambda t: t[0])
    ]

    with open(QUEUE, "w", encoding="utf-8") as f:
        f.write("\n".join(deduped) + ("\n" if deduped else ""))

    print(f"Deduped: kept {len(deduped)} item(s). Backup at logs\\queue.backup.txt")

if __name__ == "__main__":
    main()
