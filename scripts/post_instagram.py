import json
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, TwoFactorRequired

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
CLIENTS_DIR = CONFIG_DIR / "clients"
SESSIONS_DIR = CONFIG_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

def _cfg_path(client_name: str) -> Path:
    return CLIENTS_DIR / client_name / "client.json"

def _session_path(client_name: str) -> Path:
    return SESSIONS_DIR / f"{client_name}.json"

def load_client_config(client_name: str) -> dict:
    p = _cfg_path(client_name)
    if not p.exists():
        raise FileNotFoundError(f"Missing config: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def make_client() -> Client:
    cl = Client()
    cl.request_timeout = 30
    return cl

def try_session(cl: Client, client_name: str) -> bool:
    s = _session_path(client_name)
    if s.exists():
        try:
            cl.load_settings(s)
            cl.get_timeline_feed()
            return True
        except Exception:
            pass
    return False

def save_session(cl: Client, client_name: str):
    cl.dump_settings(_session_path(client_name))

def ig_login_test(client_name: str) -> dict:
    cfg = load_client_config(client_name)
    ig_user = cfg.get("IG_USERNAME")
    ig_pass = cfg.get("IG_PASSWORD")
    if not ig_user or not ig_pass:
        return {"ok": False, "via": None, "username": None, "user_id": None, "two_factor": False,
                "error": f"Missing IG_USERNAME/IG_PASSWORD for client {client_name}"}

    cl = make_client()

    if try_session(cl, client_name):
        try:
            me = cl.user_info_by_username(ig_user)
            return {"ok": True, "via": "session", "username": ig_user, "user_id": int(me.pk), "two_factor": False, "error": None}
        except Exception as e:
            return {"ok": False, "via": "session", "username": ig_user, "user_id": None, "two_factor": False, "error": str(e)}

    try:
        cl.set_device(cl.generate_device(ig_user))
        cl.login(ig_user, ig_pass)
        save_session(cl, client_name)
        me = cl.user_info_by_username(ig_user)
        return {"ok": True, "via": "password", "username": ig_user, "user_id": int(me.pk), "two_factor": False, "error": None}
    except TwoFactorRequired:
        return {"ok": False, "via": "password", "username": ig_user, "user_id": None, "two_factor": True,
                "error": "Two-factor authentication required."}
    except LoginRequired as e:
        return {"ok": False, "via": "password", "username": ig_user, "user_id": None, "two_factor": False, "error": f"Login required: {e}"}
    except Exception as e:
        return {"ok": False, "via": "password", "username": ig_user, "user_id": None, "two_factor": False, "error": str(e)}

