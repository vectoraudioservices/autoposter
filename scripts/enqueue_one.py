# scripts/enqueue_one.py
from __future__ import annotations

import importlib.util
from pathlib import Path

# Load db.py directly by path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "scripts" / "db.py"
spec = importlib.util.spec_from_file_location("db", DB_PATH)
db = importlib.util.module_from_spec(spec)
assert spec and spec.loader, "Failed to prepare db module spec"
spec.loader.exec_module(db)  # type: ignore[attr-defined]

CLIENT = "Luchiano"
FEED_PATH = Path(r"C:\content\Luchiano\feed\main_runner_demo.jpg")

def ensure_file(p: Path, size: int = 4096) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        with open(p, "wb") as f:
            f.write(b"\0" * size)

def main() -> None:
    ensure_file(FEED_PATH)
    # enqueue with new signature (kind -> content_type column)
    jid = db.add_job(
        CLIENT,
        str(FEED_PATH),
        kind="feed",
        caption="(main-runner dry demo)",
        extras={"source": "main-runner-test"},
    )
    # force eta to now so the runner considers it due
    conn = db._conn()
    now = db._now_iso()
    conn.execute("UPDATE jobs SET eta=? WHERE id=?", (now, jid))
    conn.commit()
    print(f"[enqueue_one] Enqueued job#{jid} feed -> {FEED_PATH} eta={now}")

if __name__ == "__main__":
    main()
