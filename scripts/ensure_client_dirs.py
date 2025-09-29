# scripts/ensure_client_dirs.py
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")

def main():
    if len(sys.argv) < 2:
        print("Usage: ensure_client_dirs.py <ClientName>")
        sys.exit(1)
    client = sys.argv[1]
    made = []
    for sub in ("feed", "stories", "reels", "weekly"):
        p = os.path.join(CONTENT, client, sub)
        os.makedirs(p, exist_ok=True)
        made.append(p)
    for p in made:
        print("OK", p)

if __name__ == "__main__":
    main()
