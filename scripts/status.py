import os, importlib.util, sys
from collections import defaultdict
from datetime import datetime

# --- Make Windows console reliably UTF-8 ---
if os.name == "nt":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)  # UTF-8 codepage
    except Exception:
        pass
    os.system("chcp 65001 >nul")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        try:
            sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
        except Exception:
            pass

def uprint(s=""):
    """Print that never crashes on emoji; replaces unencodable chars if needed."""
    try:
        print(s)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(s.encode(enc, errors="replace").decode(enc, errors="replace"))

# --- load db.py from same folder ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "db.py")
if not os.path.exists(DB_FILE):
    raise SystemExit(f"db.py not found at: {DB_FILE}")
spec = importlib.util.spec_from_file_location("db", DB_FILE)
db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)  # type: ignore

ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
LOGS = os.path.join(ROOT, "logs")

def read_pid(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

def pid_running(pid_str: str) -> bool:
    if not pid_str or not pid_str.isdigit():
        return False
    try:
        import subprocess
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid_str}"], capture_output=True, text=True)
        return pid_str in out.stdout
    except Exception:
        return False

def main():
    db.init_db()
    uprint("=== Autoposter Status ===")

    # processes
    wpid = read_pid(os.path.join(LOGS, "watcher.pid"))
    rpid = read_pid(os.path.join(LOGS, "runner.pid"))
    uprint(f"Watcher: {'RUNNING' if pid_running(wpid) else 'STOPPED'} (PID file: {wpid or 'n/a'})")
    uprint(f"Runner : {'RUNNING' if pid_running(rpid) else 'STOPPED'} (PID file: {rpid or 'n/a'})")
    uprint()

    # queue by client
    rows = db.list_queue()
    if not rows:
        uprint("Queue: empty")
    else:
        uprint(f"Queue items: {len(rows)}")
        per = defaultdict(list)
        for r in rows:
            per[r["client"]].append(r)
        for client, items in per.items():
            uprint(f"  {client}: {len(items)} item(s)")
            for it in items[:5]:
                cap = (it["caption"] or "").replace("\n", " / ")
                uprint(f"    - {it['eta']} | {os.path.basename(it['path'])}")
                uprint(f"      ↳ {cap[:100]}{'...' if len(cap)>100 else ''}")
    uprint()

    # today's posted (dry-run)
    today = datetime.now().strftime("%Y-%m-%d")
    posted = []
    prlog = os.path.join(LOGS, "post_runner.log")
    if os.path.exists(prlog):
        with open(prlog, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh.readlines()[-1000:]:
                if line.startswith(f"[{today}") and "POSTED (dry run):" in line:
                    posted.append(line.rstrip("\n"))
    uprint(f"Today’s posts (dry-run): {len(posted)}")
    for ln in posted[-10:]:
        uprint("  " + ln)

if __name__ == "__main__":
    main()

