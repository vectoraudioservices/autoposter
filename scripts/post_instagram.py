from __future__ import annotations
import json, os
from pathlib import Path
from instagrapi import Client

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
CLIENTS_DIR = CONFIG_DIR / "clients"
SESS_DIR = CONFIG_DIR / "sessions"
SESS_DIR.mkdir(parents=True, exist_ok=True)

def _cfg_path(client: str) -> Path:
    return CLIENTS_DIR / client / "client.json"

def _load_cfg(client: str) -> dict:
    return json.loads(_cfg_path(client).read_text(encoding="utf-8"))

def _sess_file(client: str) -> Path:
    return SESS_DIR / f"{client}.json"

def _build_client(client: str) -> Client:
    cfg = _load_cfg(client)
    user = cfg.get("IG_USERNAME")
    pw   = cfg.get("IG_PASSWORD")
    if not (user and pw):
        raise RuntimeError(f"Missing IG_USERNAME/IG_PASSWORD in {_cfg_path(client)}")

    cl = Client()
    # DO NOT set a custom device or call generate_device; let instagrapi manage it
  

    sess = _sess_file(client)
    if sess.exists():
        try:
            cl.load_settings(str(sess))
            # Private sanity check; avoids any public/GQL endpoints
            cl.account_info()
            return cl
        except Exception:
            # fall through to a fresh login
            pass

    twofa = os.getenv("IG_2FA_CODE")
    if twofa:
        cl.login(user, pw, verification_code=twofa)
    else:
        cl.login(user, pw)
    cl.dump_settings(str(sess))
    return cl

def post_photo(client: str, path: str, caption: str|None, root=None):
    return _build_client(client).photo_upload(path, caption or "")

def post_video(client: str, path: str, caption: str|None, root=None):
    return _build_client(client).video_upload(path, caption or "")

def post_reel(client: str, path: str, caption: str|None):
    return _build_client(client).clip_upload(path, caption or "")

def post_story(client: str, path: str):
    return _build_client(client).story_upload(path)
