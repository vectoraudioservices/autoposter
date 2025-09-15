import os
import subprocess
from datetime import datetime, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(ROOT, "logs")
QUEUE = os.path.join(LOGS, "queue.txt")
POST_LOG = os.path.join(LOGS, "post_runner.log")
WATCHER_PID = os.path.join(LOGS, "watcher.pid")
RUNNER_PID = os.path.join(LOGS, "runner.pid")

def read_pid(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return None

def pid_running(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        # Windows: check via tasklist
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True, text=True
        ).stdout
        return str(pid) in out and "No tasks are running" not in out
    except Exception:
        return False

def read_queue_lines():
    if not os.path.exists(QUEUE):
        return []
    with open(QUEUE, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]

def parse_queue_line(line):
    # ISO|filepath|caption(\n escaped)
    try:
        when_str, path, caption = line.split("|", 2)
        when = datetime.fromisoformat(when_str)
        # make caption preview readable
        caption = caption.replace("\\n", " / ")
        return when, path, caption
    except Exception:
        return None, None, None

def todays_posts():
    out = []
    if not os.path.exists(POST_LOG):
        return out
    today_str = date.today().strftime("%Y-%m-%d")
    with open(POST_LOG, "r", encoding="utf-8") as f:
        for ln in f:
            if ln.startswith(f"[{today_str}"):
                out.append(ln.strip())
    return out

def main():
    print("=== Autoposter Status ===")
    wpid = read_pid(WATCHER_PID)
    rpid = read_pid(RUNNER_PID)
    print(f"Watcher: {'RUNNING' if pid_running(wpid) else 'STOPPED'} (PID file: {wpid})")
    print(f"Runner : {'RUNNING' if pid_running(rpid) else 'STOPPED'} (PID file: {rpid})")
    print()

    q = read_queue_lines()
    print(f"Queue items: {len(q)}")
    for i, line in enumerate(q[:10], 1):
        when, path, caption = parse_queue_line(line)
        if when:
            print(f"  {i}. {when.strftime('%Y-%m-%d %H:%M')} | {os.path.basename(path)}")
            if caption:
                preview = caption if len(caption) <= 80 else caption[:77] + "..."
                print(f"     ↳ {preview}")
    if len(q) > 10:
        print(f"  ... and {len(q) - 10} more")
    print()

    posts = todays_posts()
    print(f"Today’s posts: {len(posts)}")
    for ln in posts[-10:]:
        print("  " + ln)

if __name__ == "__main__":
    main()
