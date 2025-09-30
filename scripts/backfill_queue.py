
from __future__ import annotations
import sys, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PY = ROOT / "scripts" / "db.py"
spec = importlib.util.spec_from_file_location("db", str(DB_PY))
db = importlib.util.module_from_spec(spec); spec.loader.exec_module(db)  # type: ignore

VALID_EXT = {".mp4", ".mov", ".jpg", ".jpeg", ".png"}

def detect_client_type(path: Path) -> tuple[str|None, str]:
    content = ROOT / "content"
    try:
        rel = path.resolve().relative_to(content)
    except Exception:
        return None, "reels"
    parts = rel.parts
    if len(parts) < 2: return None, "reels"
    client = parts[0]
    ctype = parts[1].lower()
    if ctype not in ("reels","feed","stories","weekly"):
        ctype = "reels"
    return client, ctype

def main():
    content = ROOT / "content"
    db.init_db()
    target = {sys.argv[1]} if len(sys.argv) > 1 else None
    added = skipped = 0

    for p in content.rglob("*"):
        if not p.is_file(): continue
        if p.suffix.lower() not in VALID_EXT: continue
        client, ctype = detect_client_type(p)
        if not client: continue
        if target and client not in target: continue
        full = str(p.resolve())
        if db.get_job_by_path(client, full):
            print(f"SKIP duplicate: {client} {p.name}"); skipped += 1; continue
        jid = db.add_job(client, full, content_type=ctype, caption="(backfill)", extras={"source":"backfill"})
        print(f"QUEUED job#{jid}: {p.name} (client={client}, type={ctype})"); added += 1

    print(f"Backfill complete. Queued {added}, skipped {skipped} duplicates.")

if __name__ == "__main__":
    main()
