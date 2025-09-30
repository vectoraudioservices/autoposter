# C:\autoposter\scripts\set_quotas.py
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENTS_DIR = ROOT / "config" / "clients"

def load_client_cfg(client: str) -> dict:
    p = CLIENTS_DIR / client / "client.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")), p
        except Exception:
            pass
    # default if missing or unreadable
    return {"live": False, "quotas": {}}, p

def main():
    ap = argparse.ArgumentParser(description="Set daily quotas for a client (or all clients).")
    ap.add_argument("--client", help="Client name (e.g. Luchiano). If omitted, use --all.")
    ap.add_argument("--all", action="store_true", help="Apply to ALL clients in config/clients.")
    ap.add_argument("--feed", type=int, help="feed_per_day")
    ap.add_argument("--reels", type=int, help="reels_per_day")
    ap.add_argument("--stories", type=int, help="stories_per_day")
    ap.add_argument("--weekly", type=int, help="weekly_per_day")
    ap.add_argument("--live", choices=["true","false"], help="Optionally flip live flag.")
    args = ap.parse_args()

    if not args.client and not args.all:
        ap.error("Specify --client NAME or --all")

    targets = []
    if args.all:
        if CLIENTS_DIR.exists():
            for d in CLIENTS_DIR.iterdir():
                if d.is_dir():
                    targets.append(d.name)
    if args.client:
        targets.append(args.client)

    updated = 0
    for client in targets:
        cfg, path = load_client_cfg(client)
        quotas = cfg.get("quotas") or {}

        if args.feed is not None:    quotas["feed_per_day"] = int(args.feed)
        if args.reels is not None:   quotas["reels_per_day"] = int(args.reels)
        if args.stories is not None: quotas["stories_per_day"] = int(args.stories)
        if args.weekly is not None:  quotas["weekly_per_day"] = int(args.weekly)

        cfg["quotas"] = quotas
        if args.live is not None:
            cfg["live"] = (args.live.lower() == "true")

        path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Updated {client} -> {path}")
        print(json.dumps(cfg, ensure_ascii=False, indent=2))
        updated += 1

    print(f"\nDone. Updated {updated} client file(s).")

if __name__ == "__main__":
    main()
