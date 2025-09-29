# scripts/queue_runner.py
from __future__ import annotations
import os, time, json, shutil, importlib.util
from datetime import datetime, timedelta, timezone

# ---- Efficient, safe timezone handling with fallback ----
def _load_ny_tz():
    try:
        from zoneinfo import ZoneInfo  # needs tzdata on Windows
        try:
            return ZoneInfo("America/New_York")
        except Exception:
            pass
    except Exception:
        pass
    from datetime import timedelta, timezone
    return timezone(timedelta(hours=-5))  # fallback (no DST)

NY = _load_ny_tz()
UTC = timezone.utc

# ---- Lightweight module loader (avoids package import path pitfalls) ----
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

def _load_mod(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod

db = _load_mod("db", os.path.join(SCRIPT_DIR, "db.py"))
post_instagram = _load_mod("post_instagram", os.path.join(SCRIPT_DIR, "post_instagram.py"))

CONFIG_FILE = os.path.join(ROOT, "config", "schedule.json")
LOGS_DIR = os.path.join(ROOT, "logs")
EXPORTS_DIR = os.path.join(ROOT, "exports")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

POST_LOG = os.path.join(LOGS_DIR, "post_runner.log")
with open(os.path.join(LOGS_DIR, "runner.pid"), "w", encoding="utf-8") as f:
    f.write(str(os.getpid()))

# ---- Small in-memory cache to avoid rereading config every loop ----
_CONFIG_CACHE = {"data": None, "mtime": 0.0}

def _load_config_cached() -> dict:
    try:
        st = os.stat(CONFIG_FILE)
        mtime = st.st_mtime
    except FileNotFoundError:
        return {"safe_mode": True}
    if _CONFIG_CACHE["data"] is None or _CONFIG_CACHE["mtime"] != mtime:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                _CONFIG_CACHE["data"] = json.load(f)
                _CONFIG_CACHE["mtime"] = mtime
        except Exception:
            _CONFIG_CACHE["data"] = {"safe_mode": True}
    return _CONFIG_CACHE["data"] or {"safe_mode": True}

def _ctype_from_path(p: str) -> str:
    rel = os.path.relpath(os.path.abspath(p), os.path.join(ROOT, "content"))
    parts = rel.split(os.sep)
    if len(parts) >= 2:
        ct = parts[1].lower()
        if ct in ("feed", "stories", "reels", "weekly"):
            return ct
    return "feed"

def _fmt_local(iso_utc: str) -> str:
    # tolerant parsing (with/without Z)
    dt = datetime.fromisoformat(iso_utc.replace("Z", ""))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(NY).strftime("%Y-%m-%d %H:%M")

def log(msg: str):
    stamp = datetime.now(tz=NY).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    with open(POST_LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

def _load_client_cfg(client: str) -> dict:
    p = os.path.join(ROOT, "config", "clients", client, "client.json")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"live": False}

def _limits(ccfg: dict):
    # simple per-type daily caps; adjust as needed
    return {
        "feed":   max(0, int(ccfg.get("daily_quota", 2))),
        "stories":max(0, int(ccfg.get("stories_daily_quota", 5))),
        "reels":  max(0, int(ccfg.get("reels_daily_quota", 2))),
        "weekly": max(0, int(ccfg.get("weekly_quota", 1))),
    }

def _today_count(client: str, ctype: str) -> int:
    # counts 'done' posts for (client, ctype) on *local* day
    today = datetime.now(tz=NY).strftime("%Y-%m-%d")
    with db.get_conn() as c:
        rows = c.execute("SELECT path, posted_at FROM jobs WHERE client=? AND status='done'", (client,)).fetchall()
    used = 0
    for r in rows:
        pa = r["posted_at"]
        if not pa:
            continue
        try:
            dt = datetime.fromisoformat(pa)
        except Exception:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        if dt.astimezone(NY).strftime("%Y-%m-%d") == today and _ctype_from_path(r["path"]) == ctype:
            used += 1
    return used

def _next_day_utc(hour_local=11) -> str:
    local = datetime.now(tz=NY).replace(hour=hour_local, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return local.astimezone(UTC).isoformat()

def _dry_copy(path: str):
    base = os.path.basename(path)
    target = os.path.join(EXPORTS_DIR, base)
    try:
        if os.path.exists(path):
            shutil.copyfile(path, target)
        else:
            open(target, "wb").close()
    except Exception:
        pass

def _post_live(client: str, path: str, caption: str, ctype: str) -> str:
    lower = path.lower()
    if lower.endswith(".mp4"):
        # posts video/Reel; can be expanded with cover image if present
        return post_instagram.post_video(client, path, caption, ROOT)
    else:
        return post_instagram.post_photo(client, path, caption, ROOT)

def main():
    db.init_db()
    cfg = _load_config_cached()
    safe_mode = bool(cfg.get("safe_mode", True))
    log(f"Queue runner started. Checking every 15s… (SAFE_MODE={'ON' if safe_mode else 'OFF'})")

    sleep_idle = 15
    sleep_busy = 3

    while True:
        due = db.get_due_jobs(limit=50)
        if not due:
            time.sleep(sleep_idle)
            continue

        for row in due:
            job_id = row["id"]; client = row["client"]; path = row["path"]; caption = row["caption"]; eta = row["eta"]
            ctype = _ctype_from_path(path)
            ccfg  = _load_client_cfg(client)
            limits = _limits(ccfg)
            used = _today_count(client, ctype)
            limit = limits.get(ctype, 0)

            if limit == 0:
                new_eta = _next_day_utc(11)
                db.reschedule(job_id, new_eta, f"limit=0 for {client}/{ctype}")
                log(f"SKIP (limit=0) {client}/{ctype}. Rescheduled job#{job_id} -> { _fmt_local(new_eta) }")
                continue

            if used >= limit:
                new_eta = _next_day_utc(11)
                db.reschedule(job_id, new_eta, f"quota reached {used}/{limit} for {client}/{ctype}")
                log(f"QUOTA REACHED: {client}/{ctype} ({used}/{limit}). Rescheduled job#{job_id} -> { _fmt_local(new_eta) }")
                continue

            live_allowed = (not safe_mode) and bool(ccfg.get("live", False))
            db.mark_in_progress(job_id)
            log(f"PARSED: when={_fmt_local(eta)} | file={os.path.basename(path)} | client={client} | type={ctype} | used={used}/{limit} | mode={'LIVE' if live_allowed else 'DRY'}")

            try:
                if live_allowed:
                    media_id = _post_live(client, path, caption, ctype)
                    log(f"POSTED (LIVE): {os.path.basename(path)} | CLIENT: {client} | TYPE: {ctype} | media_id={media_id}")
                else:
                    _dry_copy(path)
                    log(f"POSTED (dry run): {os.path.basename(path)} | CLIENT: {client} | TYPE: {ctype} | CAPTION: {caption.replace(chr(10),' / ')}")
                db.mark_done(job_id)

            except Exception as e:
                # retry later with reason persisted
                new_eta = (datetime.now(tz=UTC) + timedelta(minutes=30)).isoformat()
                db.reschedule(job_id, new_eta, f"{type(e).__name__}: {e}")
                log(f"POST FAILURE [{client}/{ctype}]: {e}. RESCHEDULED job#{job_id} -> { _fmt_local(new_eta) }")

        time.sleep(sleep_busy)

if __name__ == "__main__":
    main()


