import os
import json
import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Paths & folders ---
ROOT = os.path.dirname(os.path.abspath(__file__))
FOLDERS = ["content", "logs", "scripts", "exports", "config"]
for f in FOLDERS:
    os.makedirs(os.path.join(ROOT, f), exist_ok=True)

CONTENT_DIR = os.path.join(ROOT, "content")
LOGS_DIR = os.path.join(ROOT, "logs")
CONFIG_DIR = os.path.join(ROOT, "config")
LOG_FILE = os.path.join(LOGS_DIR, "autoposter.log")

CLIENTS_FILE = os.path.join(CONFIG_DIR, "clients.json")
CURRENT_CLIENT_FILE = os.path.join(CONFIG_DIR, "current_client.txt")

# --- Logging ---
def log(message: str):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

# --- PID file ---
WATCHER_PID_FILE = os.path.join(LOGS_DIR, "watcher.pid")
try:
    with open(WATCHER_PID_FILE, "w", encoding="utf-8") as _pf:
        _pf.write(str(os.getpid()))
except Exception:
    pass

# --- Helpers for client profiles ---
def load_clients() -> dict:
    try:
        with open(CLIENTS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        log(f"CLIENTS LOAD WARN: {e}")
        return {}

def load_current_client_name() -> str:
    try:
        with open(CURRENT_CLIENT_FILE, "r", encoding="utf-8") as fh:
            name = fh.read().strip()
            return name or "VectorManagement"
    except Exception:
        return "VectorManagement"

def infer_client_from_path(abs_path: str) -> str:
    """If file is under content/<Client>/..., return <Client> else fallback."""
    try:
        rel = os.path.relpath(abs_path, CONTENT_DIR)
        first = rel.split(os.sep, 1)[0]
        if first and first not in (".", "") and first.lower() != os.path.basename(CONTENT_DIR).lower():
            return first
    except Exception:
        pass
    return load_current_client_name()

# --- Event handler ---
class NewContentHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        time.sleep(0.5)  # let file finish writing

        filename = os.path.basename(event.src_path)
        abs_path = os.path.abspath(event.src_path)
        client_name = infer_client_from_path(abs_path)

        log(f"NEW FILE DETECTED: {os.path.relpath(abs_path, CONTENT_DIR)}")
        log(f"READY TO PROCESS: {filename} (client={client_name})")

        # Generate a simple caption
        caption = f"🔥 New drop • {datetime.now().strftime('%b %d')}\nFollow @VectorManagement for daily drops. 🚀"
        try:
            from scripts.scheduler import add_to_queue
            eta = add_to_queue(abs_path, caption, minutes_from_now=10)
            log(f"SCHEDULED: {filename} at {eta.strftime('%Y-%m-%d %H:%M')} (client={client_name})")
        except Exception as e:
            log(f"SCHEDULE ERROR: {e}")

if __name__ == "__main__":
    log("Startup: verified folder structure.")
    log("Watching /content for new files...")
    event_handler = NewContentHandler()
    observer = Observer()
    # recursive=True so client subfolders work
    observer.schedule(event_handler, CONTENT_DIR, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Shutdown requested. Stopping watcher...")
        observer.stop()
    observer.join()







