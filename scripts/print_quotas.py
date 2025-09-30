# C:\autoposter\scripts\print_quotas.py
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENTS_DIR = ROOT / "config" / "clients"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    args = ap.parse_args()

    p = CLIENTS_DIR / args.client / "client.json"
    if not p.exists():
        print(f"Not found: {p}")
        return
    cfg = json.loads(p.read_text(encoding="utf-8"))
    quotas = cfg.get("quotas", {})
    print(f"Client: {args.client}")
    print(f" live: {cfg.get('live', False)}")
    print(" quotas:")
    print(f"   feed_per_day:    {quotas.get('feed_per_day', 1)}")
    print(f"   reels_per_day:   {quotas.get('reels_per_day', 2)}")
    print(f"   stories_per_day: {quotas.get('stories_per_day', 3)}")
    print(f"   weekly_per_day:  {quotas.get('weekly_per_day', 1)}")

if __name__ == "__main__":
    main()
