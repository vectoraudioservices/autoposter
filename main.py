import os, time, threading
from datetime import datetime
from pathlib import Path
from watchdog.events import FileSystemEventHandler
try:
    from watchdog.observers import Observer as _Obs
except Exception:
    from watchdog.observers.polling import PollingObserver as _Obs

from scripts import db

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
LOGS = ROOT / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

def log(msg: str):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    with open(LOGS / "autoposter.log", "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

IGNORE_NAMES = {"thumbs.db", ".ds_store"}
IGNORE_PREFIX = ("~$",)
IGNORE_EXT = {".tmp", ".part", ".crdownload"}
VALID_EXT  = {".mp4", ".mov", ".jpg", ".jpeg", ".png"}

PENDING = {}
LOCK = threading.Lock()
DEBOUNCE_SEC = 1.0

def _detect_client_type(path: Path) -> tuple[str|None, str]:
    try:
        rel = path.resolve().relative_to(CONTENT)
    except Exception:
        return None, "reels"
    parts = rel.parts
    if len(parts) < 2: return None, "reels"
    client = parts[0]
    ctype = parts[1].lower()
    if ctype not in ("reels","feed","stories","weekly"):
        ctype = "reels"
    return client, ctype

def handle_new_file(path: Path):
    if not path.is_file(): return
    name = path.name.lower()
    if name in IGNORE_NAMES: return
    if path.suffix.lower() not in VALID_EXT: return
    if name.startswith(IGNORE_PREFIX) or path.suffix.lower() in IGNORE_EXT: return

    client, ctype = _detect_client_type(path)
    if not client:
        log(f"⚠️ Ignoring file outside content/<Client>/<type>/: {path}")
        return

    full = str(path.resolve())
    caption = f"🔥 New drop • {datetime.now():%b %d}\nFollow @VectorManagement"

    try:
        db.init_db()
        existing = db.get_job_by_path(client, full)
        if existing:
            log(f"🔁 Duplicate ignored (already in DB status={existing['status']}): {path.name}")
            return

        job_id = db.add_job(client, full, content_type=ctype, caption=caption, extras={"source":"watcher"})
        log(f"📦 QUEUED job#{job_id}: {path.name} (client={client}, type={ctype})")
    except Exception as e:
        log(f"❌ Failed enqueue {path}: {e}")

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory: return
        p = Path(event.src_path)
        with LOCK: PENDING[p] = time.time()
    def on_modified(self, event):
        if event.is_directory: return
        p = Path(event.src_path)
        with LOCK: PENDING[p] = time.time()

def debouncer_loop():
    while True:
        time.sleep(0.5)
        now = time.time()
        emit = []
        with LOCK:
            for p, t0 in list(PENDING.items()):
                if now - t0 >= DEBOUNCE_SEC:
                    emit.append(p)
                    del PENDING[p]
        for p in emit:
            handle_new_file(p)

def main():
    CONTENT.mkdir(parents=True, exist_ok=True)
    db.init_db()
    with open(LOGS / "watcher.pid", "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    log("Watcher startup OK.")
    observer = _Obs()
    handler = Handler()
    observer.schedule(handler, str(CONTENT), recursive=True)
    observer.start()
    log("👀 Watching /content for new files...")
    threading.Thread(target=debouncer_loop, daemon=True).start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
