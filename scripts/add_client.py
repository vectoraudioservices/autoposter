import os, json, argparse, re
from datetime import datetime

# --- paths ---
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(ROOT, "config")
CLIENTS_DIR = os.path.join(CONFIG_DIR, "clients")
CONTENT_DIR = os.path.join(ROOT, "content")
LIMITS_FILE = os.path.join(CONFIG_DIR, "client_limits.json")

# --- utils ---
def slugify(name: str) -> str:
    # keep letters, numbers, underscore; replace spaces with underscore
    s = re.sub(r"\s+", "_", name.strip())
    s = re.sub(r"[^A-Za-z0-9_]", "", s)
    return s or "Client"

def ensure_dirs(path: str):
    os.makedirs(path, exist_ok=True)

def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except Exception:
        return default

def save_json(path: str, data):
    ensure_dirs(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def append_if_missing_quota(client: str, quota: int):
    data = load_json(LIMITS_FILE, {"default_daily_quota": 3, "clients": {}})
    if "default_daily_quota" not in data: data["default_daily_quota"] = 3
    if "clients" not in data: data["clients"] = {}
    data["clients"][client] = max(1, int(quota))
    save_json(LIMITS_FILE, data)

def main():
    ap = argparse.ArgumentParser(description="Add a new client to Autoposter")
    ap.add_argument("name", help="Client name (will create content/<name> and config/clients/<name>)")
    ap.add_argument("--quota", type=int, default=1, help="Daily post limit for this client (default: 1)")
    ap.add_argument("--hours", nargs="*", type=int, default=[], help="Preferred posting hours (24h). Ex: --hours 11 15 19")
    ap.add_argument("--ig-username", default="", help="Instagram username (optional)")
    ap.add_argument("--ig-password", default="", help="Instagram password (optional)")
    args = ap.parse_args()

    client = slugify(args.name)
    client_cfg_dir = os.path.join(CLIENTS_DIR, client)
    ensure_dirs(client_cfg_dir)

    # 1) content folder
    ensure_dirs(os.path.join(CONTENT_DIR, client))

    # 2) per-client config (hours & quota stored here too)
    cfg = {
        "name": client,
        "created": datetime.now().isoformat(timespec="seconds"),
        "hours_24": sorted(list(set(h for h in args.hours if 0 <= h <= 23))) if args.hours else [],
        "daily_quota": max(1, int(args.quota))
    }
    save_json(os.path.join(client_cfg_dir, "client.json"), cfg)

    # 3) per-client secrets
    secrets_path = os.path.join(client_cfg_dir, "secrets.env")
    if not os.path.exists(secrets_path):
        with open(secrets_path, "w", encoding="utf-8") as f:
            f.write("IG_USERNAME={}\n".format(args.ig_username))
            f.write("IG_PASSWORD={}\n".format(args.ig_password))
            f.write("IG_2FA_CODE=\n")
    # never print secrets

    # 4) quotas file (so runner respects it today)
    append_if_missing_quota(client, cfg["daily_quota"])

    print("✅ Client created:")
    print(f" - content\\{client}\\")
    print(f" - config\\clients\\{client}\\client.json")
    print(f" - config\\clients\\{client}\\secrets.env")
    print(f" - quota set to {cfg['daily_quota']} in config\\client_limits.json")
    if cfg["hours_24"]:
        print(f" - preferred hours: {cfg['hours_24']}")
    else:
        print(" - preferred hours: (none set; will use default hours from config\\schedule.json)")

if __name__ == "__main__":
    main()
