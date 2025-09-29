import json
import time
import inspect
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Your DB helpers
import scripts.db as db

CONTENT_ROOT = Path("content")
CLIENTS_JSON = Path("config/clients.json")
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv"}


def load_known_clients():
    if not CLIENTS_JSON.exists():
        return set()
    try:
        data = json.loads(CLIENTS_JSON.read_text(encoding="utf-8"))
        return set(data.keys())
    except Exception:
        return set()


def ensure_folders(clients: set[str]):
    for c in clients:
        for sub in ("reels", "feed", "stories"):
            (CONTENT_ROOT / c / sub).mkdir(parents=True, exist_ok=True)


def infer_client(known_clients: set[str], file_path: Path):
    """Determine client from folder: content/<Client>/<type>/<file>"""
    try:
        rel = file_path.resolve().relative_to(CONTENT_ROOT.resolve())
    except Exception:
        return None
    parts = list(rel.parts)
    if len(parts) >= 3:
        maybe_client, maybe_type = parts[0], parts[1]
        if maybe_client in known_clients and maybe_type in {"reels", "feed", "stories"}:
            return maybe_client
    return None


def add_job_flex(conn, client: str, file_path: str):
    """
    Call scripts.db.add_job with only the params it actually accepts.
    Supports variants like:
      - add_job(conn, client, file)
      - add_job(conn, client, file, caption=None)
      - add_job(conn, client, file, eta_iso_utc=None)
      - add_job(conn, client, file, when=None, caption=None)
    """
    fn = db.add_job
    sig = inspect.signature(fn)
    params = list(sig.parameters.items())

    # Required base positional args we can always provide in order:
    base_positional = [conn, client, file_path]

    # Build kwargs ONLY for names that exist (avoid "multiple values" errors)
    extra_kwargs = {}
    for name, param in params[3:]:
        # Only pass explicit names we recognize and set them to None by default
        if name in ("caption", "cap", "text"):
            extra_kwargs[name] = None
        elif name in ("eta_iso_utc", "when", "when_utc", "scheduled_at", "schedule_at"):
            extra_kwargs[name] = None
        # else: ignore unknown optional params (db layer will set defaults)

    return fn(*base_positional, **extra_kwargs)


class MediaHandler(FileSystemEventHandler):
    def __init__(self, conn, known_clients: set[str]):
        super().__init__()
        self.conn = conn
        self.known_clients = known_clients

    def _enqueue(self, file_path: Path):
        if file_path.suffix.lower() not in VIDEO_EXTS:
            return
        client = infer_client(self.known_clients, file_path)
        if not client:
            print(f"⚠️ Skipping {file_path}: cannot determine client (use content/<Client>/(reels|feed|stories)/)")
            return
        try:
            qid = add_job_flex(self.conn, client, str(file_path.resolve()))
            print(f"✅ Enqueued for {client}: {file_path.name} (queue_id={qid})")
        except Exception as e:
            print(f"❌ Failed enqueue {file_path}: {e}")

    def on_created(self, event):
        if not event.is_directory:
            self._enqueue(Path(event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            self._enqueue(Path(event.dest_path))


def main():
    known = load_known_clients()
    ensure_folders(known)
    print(f"👀 Multi-client Watcher running. Known clients: {', '.join(sorted(known)) or '(none)'}")
    print("   Drop files under: content/<Client>/(reels|feed|stories)/")

    conn = db.get_conn()
    handler = MediaHandler(conn, known)
    observer = Observer()
    # One recursive watcher over content/ handles all clients & subfolders
    observer.schedule(handler, str(CONTENT_ROOT), recursive=True)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
