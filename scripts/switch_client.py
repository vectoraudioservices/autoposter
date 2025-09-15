import os
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(ROOT, "config")
CLIENTS_FILE = os.path.join(CONFIG_DIR, "clients.json")
CURRENT_FILE = os.path.join(CONFIG_DIR, "current_client.txt")

def read_clients() -> dict:
    try:
        with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts\\switch_client.py <ClientName>")
        print("Examples:")
        print("  python scripts\\switch_client.py VectorManagement")
        print("  python scripts\\switch_client.py MerkabaEntertainment")
        sys.exit(1)

    target = sys.argv[1].strip()
    clients = read_clients()
    if target not in clients:
        print(f"ERROR: '{target}' not found in config\\clients.json.")
        print("Available clients:")
        for name in sorted(clients.keys()):
            print(f" - {name}")
        sys.exit(2)

    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CURRENT_FILE, "w", encoding="utf-8") as f:
        f.write(target)

    print(f"Current client set to: {target}")

if __name__ == "__main__":
    main()
