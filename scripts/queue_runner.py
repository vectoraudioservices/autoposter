import os
import json
import time
from datetime import datetime
from typing import List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT, "config", "schedule.json")
LOGS_DIR = os.path.join(ROOT, "logs")
QUEUE_FILE = os.path.join(LOGS_DIR, "queue.txt")
POST_LOG = os.path.join(LOGS_DIR, "post_runner.log")
EXPORTS_DIR = os.path.join(ROOT, "exports")

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

RUNNER_PID_FILE = os.path.join(LOGS_DIR, "runner.pid")
try:
    with open(RUNNER_PID_FILE, "w", encoding="utf-8") as _pf:
        _pf.write(str(os.getpid()))
except Exception:
    pass

def load_config() -> dict:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {
            "safe_mode": True,
            "platforms": {},
            "best_times": {"default_hours_24": [11, 15, 19]},
        }

def log(msg: str):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    with open(POST_LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

def read_queue() -> List[str]:
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE, "r", encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip()]

def infer_client_from_path(path: str) -> str:
    """Infer client key from content\<Client>\... path; fallback to current_client.txt; default VectorManagement."""
    try:
        content_dir = os.path.join(ROOT, "content")
        rel = os.path.relpath(path, content_dir)
        first = rel.split(os.sep, 1)[0]
        if first and first not in (".", "") and first.lower() != os.path.basename(content_dir).lower():
            return first
    except Exception:
        pass
    try:
        with open(os.path.join(ROOT, "config", "current_client.txt"), "r", encoding="utf-8") as f:
            name = f.read().strip()
            return name or "VectorManagement"
    except Exception:
        return "VectorManagement"

def parse_line(line: str) -> Tuple[datetime, str, str, str]:
    """
    Format (new): ISO|path|caption_with_\\n|client=<ClientKey>
    Format (old): ISO|path|caption_with_real_breaks   (no client tag)
    Returns: (when, path, caption, client)
    """
    try:
        parts = line.split("|", 3)
        when = datetime.fromisoformat(parts[0])
        path = parts[1]
        caption = parts[2].replace("\\n", "\n")  # decode escaped \n to real newlines

        client = None
        if len(parts) >= 4 and parts[3].startswith("client="):
            client = parts[3].split("=", 1)[1].strip() or None

        if not client:
            # old line: infer from path
            client = infer_client_from_path(path)

        return when, path, caption, client
    except Exception as e:
        log(f"SKIP BAD LINE: {e} :: {line}")
        return datetime.max, "", "", "VectorManagement"

def write_queue(lines: List[str]):
    with open(QUEUE_FILE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + ("\n" if lines else ""))

def dry_run_post(filepath: str, caption: str, client: str):
    try:
        base = os.path.basename(filepath)
        target = os.path.join(EXPORTS_DIR, base)
        if os.path.exists(filepath):
            with open(filepath, "rb") as src, open(target, "wb") as dst:
                dst.write(src.read())
        else:
            with open(target, "wb") as dst:
                dst.write(b"")
        preview = caption.replace("\n", " / ")
        log(f"POSTED (dry run): {os.path.basename(filepath)}  |  CLIENT: {client}  |  CAPTION: {preview}")
    except Exception as e:
        log(f"POST ERROR: {e}")

def real_post_dispatch(filepath: str, caption: str, cfg: dict, client: str):
    platforms = cfg.get("platforms", {}) or {}
    preview = caption.replace("\n", " / ")

    # Instagram only (others off for now)
    if platforms.get("instagram"):
        try:
            from post_instagram import post_instagram
            result = post_instagram(filepath, preview, client_name=client)
            log(result)
            return
        except Exception as e:
            log(f"INSTAGRAM ERROR [{client}]: {e}")

    # Placeholder if nothing posted:
    log(f"POSTED (real mode placeholder): {os.path.basename(filepath)}  |  CLIENT: {client}  |  CAPTION: {preview}")

def main():
    cfg = load_config()
    safe_mode = bool(cfg.get("safe_mode", True))
    log(f"Queue runner started. Checking every 15s… (SAFE_MODE={'ON' if safe_mode else 'OFF'})")

    while True:
        lines = read_queue()
        if not lines:
            time.sleep(15)
            continue

        remaining = []
        now = datetime.now()
        for line in lines:
            when, path, caption, client = parse_line(line)
            if when == datetime.max or not path:
                continue

            # Trace what we parsed for easier debugging
            log(f"PARSED: when={when.isoformat()} | file={os.path.basename(path)} | client={client}")

            if when <= now:
                if safe_mode:
                    dry_run_post(path, caption, client)
                else:
                    real_post_dispatch(path, caption, cfg, client)
            else:
                remaining.append(line)

        write_queue(remaining)
        time.sleep(15)

if __name__ == "__main__":
    main()



