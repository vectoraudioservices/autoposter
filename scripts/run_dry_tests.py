# scripts/run_dry_tests.py
from __future__ import annotations

import os
import subprocess
import importlib.util
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
DB_PATH = SCRIPTS / "db.py"

# Load db by absolute path (no package import required)
spec = importlib.util.spec_from_file_location("db", DB_PATH)
db = importlib.util.module_from_spec(spec)
assert spec and spec.loader, "Failed to prepare db module spec"
spec.loader.exec_module(db)  # type: ignore[attr-defined]

VENV_PY = (PROJECT_ROOT / "venv" / "Scripts" / "python.exe").as_posix()

CLIENT = "Luchiano"
FEED_DIR   = Path(r"C:\content\Luchiano\feed")
REELS_DIR  = Path(r"C:\content\Luchiano\reels")
STORY_DIR  = Path(r"C:\content\Luchiano\stories")

def ensure_dirs() -> None:
    FEED_DIR.mkdir(parents=True, exist_ok=True)
    REELS_DIR.mkdir(parents=True, exist_ok=True)
    STORY_DIR.mkdir(parents=True, exist_ok=True)

def make_dummy(path: Path, size: int = 4096) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Create a small file if missing
    if not path.exists():
        with open(path, "wb") as f:
            f.write(b"\0" * size)

def enqueue_samples() -> List[int]:
    """Enqueue one feed, one reels, one story; return list of job ids."""
    jobs: List[int] = []
    feed_path  = FEED_DIR / "dry_demo_feed.jpg"
    reels_path = REELS_DIR / "dry_demo_reel.mp4"
    story_path = STORY_DIR / "dry_demo_story.jpg"

    make_dummy(feed_path,  4096)
    make_dummy(reels_path, 8192)
    make_dummy(story_path, 4096)

    # Use the new add_job signature with kind=
    jobs.append(db.add_job(CLIENT, str(feed_path),  kind="feed",   caption="(dry feed)",   extras={"source":"dry-test"}))
    jobs.append(db.add_job(CLIENT, str(reels_path), kind="reels",  caption="(dry reels)",  extras={"source":"dry-test"}))
    jobs.append(db.add_job(CLIENT, str(story_path), kind="stories",caption="(dry story)",  extras={"source":"dry-test"}))
    return jobs

def force_eta_now(job_ids: List[int]) -> None:
    conn = db._conn()
    now = db._now_iso()
    qmarks = ",".join("?" for _ in job_ids)
    params = [now] + job_ids
    conn.execute(f"UPDATE jobs SET eta = ? WHERE id IN ({qmarks})", params)
    conn.commit()

def run_demo_once() -> str:
    # Run the quota-ignoring demo runner once (DRY), capture output
    cmd = [VENV_PY, (SCRIPTS / "queue_runner_demo.py").as_posix(), "--client", CLIENT, "--dry-run", "--once"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return (res.stdout or "") + (res.stderr or "")

def list_recent(n: int = 10) -> List[Tuple[int, str, str, str]]:
    """Return recent jobs tuples (id, type, status, path)."""
    conn = db._conn()
    rows = conn.execute(
        f"""
        SELECT id, content_type, status, path
        FROM jobs
        WHERE client = ?
        ORDER BY id DESC
        LIMIT {n}
        """,
        (CLIENT,),
    ).fetchall() or []
    return [(int(r["id"]), r["content_type"], r["status"], r["path"]) for r in rows]

def main() -> None:
    print("[dry-tests] start")
    ensure_dirs()
    job_ids = enqueue_samples()
    print(f"[dry-tests] enqueued jobs: {job_ids}")

    # Make them due now
    force_eta_now(job_ids)
    print("[dry-tests] forced ETA=now")

    # Process up to three times (feed, reels, story)
    outputs: List[str] = []
    for i in range(3):
        out = run_demo_once()
        outputs.append(out)
        print(f"[dry-tests] run {i+1} output:\n{out.strip()}\n")

    # Summarize last 10 jobs
    recent = list_recent(10)
    print("[dry-tests] recent jobs (id, type, status, path tail):")
    for jid, kind, status, path in recent:
        tail = str(path).replace("\\", "/").split("/")[-1]
        print(f"  #{jid:>4}  {kind:<7}  {status:<11}  {tail}")

    # Final assertion: all three test jobs should be done
    conn = db._conn()
    rows = conn.execute(
        f"SELECT id, status FROM jobs WHERE id IN ({','.join('?' for _ in job_ids)})",
        job_ids,
    ).fetchall()
    done = all((r["status"] == "done") for r in rows)
    print(f"\n[dry-tests] PASS={done} (all test jobs marked done)")

if __name__ == "__main__":
    main()
