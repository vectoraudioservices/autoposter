# scripts/pre_demo_quickcheck.py
from __future__ import annotations

import json
import importlib.util
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
DB_PATH = SCRIPTS / "db.py"

def load_db():
    spec = importlib.util.spec_from_file_location("db", DB_PATH)
    db = importlib.util.module_from_spec(spec)
    assert spec and spec.loader, "Failed to prepare db module spec"
    spec.loader.exec_module(db)  # type: ignore[attr-defined]
    return db

def check_paths(client: str) -> Dict[str, Any]:
    issues = []
    info: Dict[str, Any] = {}

    # Content folders
    feed = Path(rf"C:\content\{client}\feed")
    reels = Path(rf"C:\content\{client}\reels")
    stories = Path(rf"C:\content\{client}\stories")
    for p in (feed, reels, stories):
        info[str(p)] = p.exists()
        if not p.exists():
            issues.append(f"Missing folder: {p}")

    # Client config
    cfg_path = PROJECT_ROOT / "config" / "clients" / client / "client.json"
    info[str(cfg_path)] = cfg_path.exists()
    if not cfg_path.exists():
        issues.append(f"Missing client config: {cfg_path}")
        cfg = {}
    else:
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append(f"Bad JSON in {cfg_path}: {e}")
            cfg = {}

    # Session file
    sess_path = PROJECT_ROOT / "config" / "sessions" / f"{client}.json"
    info[str(sess_path)] = sess_path.exists()
    if not sess_path.exists():
        issues.append(f"Missing session file: {sess_path}")

    return {
        "info": info,
        "issues": issues,
        "cfg": cfg,
        "paths": {"feed": str(feed), "reels": str(reels), "stories": str(stories)},
        "cfg_path": str(cfg_path),
        "sess_path": str(sess_path),
    }

def summarize_jobs(db, client: str) -> str:
    conn = db._conn()
    rows = conn.execute(
        """
        SELECT status, COUNT(*) as c
        FROM jobs
        WHERE client = ?
        GROUP BY status
        """,
        (client,),
    ).fetchall() or []
    counts = {r["status"]: int(r["c"]) for r in rows}
    queued = counts.get("queued", 0)
    inprog = counts.get("in_progress", 0)
    done = counts.get("done", 0)

    err = conn.execute(
        "SELECT COUNT(*) AS c FROM jobs WHERE client=? AND error IS NOT NULL AND error <> ''",
        (client,),
    ).fetchone() or {"c": 0}
    errors = int(err["c"])

    recent = conn.execute(
        """
        SELECT id, content_type, status, path, eta
        FROM jobs WHERE client = ?
        ORDER BY id DESC LIMIT 5
        """,
        (client,),
    ).fetchall() or []

    lines = [
        f"Jobs summary for {client}: queued={queued}, in_progress={inprog}, done={done}, errors={errors}",
        "Recent 5:",
    ]
    for r in recent:
        tail = str(r["path"]).replace("\\", "/").split("/")[-1]
        lines.append(f"  #{r['id']:>4}  {r['content_type']:<7} {r['status']:<11} eta={r['eta']}  {tail}")
    return "\n".join(lines)

def main():
    client = "Luchiano"
    print("[pre-demo] Starting quick check...")
    db = load_db()

    # DB touch
    try:
        conn = db._conn()
        conn.execute("SELECT 1").fetchone()
        print("[pre-demo] DB connection: OK")
    except Exception as e:
        print(f"[pre-demo] DB connection: FAIL -> {e}")

    # Paths & config
    chk = check_paths(client)
    for k, v in chk["info"].items():
        print(f"[pre-demo] Exists: {k} -> {v}")

    # Key config fields
    cfg = chk["cfg"]
    if cfg:
        mpd = (cfg.get("max_per_day") or {})
        print(f"[pre-demo] Config: max_per_day keys -> {list(mpd.keys())}")
    else:
        print("[pre-demo] Config: (missing or invalid)")

    if chk["issues"]:
        print("\n[pre-demo] Issues detected:")
        for i in chk["issues"]:
            print(" - " + i)
    else:
        print("\n[pre-demo] No blocking issues detected.")

    # Jobs summary
    print("\n" + summarize_jobs(db, client))

if __name__ == "__main__":
    main()
