import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "logs", "queue.txt")

def parse_line(line: str):
    parts = line.split("|", 3)
    if len(parts) < 3:
        raise ValueError("too few parts")
    when = datetime.fromisoformat(parts[0])
    path = parts[1]
    caption = parts[2].replace("\\n", "\n")
    client = "VectorManagement"
    if len(parts) == 4 and parts[3].startswith("client="):
        client = parts[3].split("=", 1)[1].strip() or "VectorManagement"
    return when, path, caption, client

def main():
    if not os.path.exists(QUEUE):
        print("queue.txt not found.")
        return
    with open(QUEUE, "r", encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh if ln.strip()]
    if not lines:
        print("queue.txt is empty.")
        return
    print(f"Items in queue.txt: {len(lines)}\n")
    for i, line in enumerate(lines, 1):
        try:
            when, path, caption, client = parse_line(line)
            caption_preview = caption[:120].replace("\n", " / ")
            if len(caption) > 120:
                caption_preview += "..."
            print(f"{i}. {when} | client={client}")
            print(f"   PATH: {path}")
            print(f"   FILE: {os.path.basename(path)}")
            print(f"   ↳ {caption_preview}")
        except Exception as e:
            print(f"{i}. **BAD LINE** ({e}): {line}")

if __name__ == "__main__":
    main()


