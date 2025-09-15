import os
import json
from instagrapi import Client

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(ROOT, "logs")
CONFIG_DIR = os.path.join(ROOT, "config")

# Legacy (global) locations for backward compatibility
GLOBAL_SECRETS = os.path.join(CONFIG_DIR, "secrets.env")
GLOBAL_SESSION = os.path.join(LOGS_DIR, "ig_session.json")

def _load_env(path: str) -> dict:
    env = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln or ln.startswith("#") or "=" not in ln:
                    continue
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def _client_paths(client_name: str | None):
    """
    Return (secrets_path, session_path) for the given client.
    If client_name is None, fall back to global legacy paths.
    """
    if not client_name:
        return GLOBAL_SECRETS, GLOBAL_SESSION
    base = os.path.join(CONFIG_DIR, "clients", client_name)
    secrets = os.path.join(base, "secrets.env")
    sessions_dir = os.path.join(LOGS_DIR, "sessions")
    os.makedirs(sessions_dir, exist_ok=True)
    session = os.path.join(sessions_dir, f"ig_session_{client_name}.json")
    return secrets, session

def _save_session(cl: Client, session_path: str):
    data = cl.get_settings()
    with open(session_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)

def _load_session(cl: Client, session_path: str) -> bool:
    if not os.path.exists(session_path):
        return False
    try:
        with open(session_path, "r", encoding="utf-8") as fh:
            settings = json.load(fh)
        cl.set_settings(settings)
        cl.get_timeline_feed()  # light ping to validate
        return True
    except Exception:
        return False

def _ensure_logged_in(cl: Client, client_name: str | None = None):
    secrets_path, session_path = _client_paths(client_name)
    env = _load_env(secrets_path)
    username = env.get("IG_USERNAME", "")
    password = env.get("IG_PASSWORD", "")
    twofa_code = env.get("IG_2FA_CODE") or None

    if not username or not password:
        loc = f"config\\clients\\{client_name}\\secrets.env" if client_name else "config\\secrets.env"
        raise RuntimeError(f"Missing IG_USERNAME or IG_PASSWORD in {loc}")

    # Try existing session first
    if _load_session(cl, session_path):
        return

    # Fresh login (2FA optional)
    if twofa_code:
        cl.login(username, password, verification_code=twofa_code)
    else:
        cl.login(username, password)

    _save_session(cl, session_path)

def ig_login_test(client_name: str | None = None) -> str:
    """
    Verifies login/session and returns username.
    If client_name is provided, uses that client's secrets + session.
    """
    cl = Client()
    _ensure_logged_in(cl, client_name=client_name)
    me = cl.account_info()
    return f"Login OK as @{me.username}" + (f" (client={client_name})" if client_name else "")

def post_instagram(filepath: str, caption: str, client_name: str | None = None) -> str:
    """
    Posts photo/video to Instagram Feed for given client (or global if None).
    """
    cl = Client()
    _ensure_logged_in(cl, client_name=client_name)

    lower = (filepath or "").lower()
    if lower.endswith((".jpg", ".jpeg", ".png")):
        media = cl.photo_upload(path=filepath, caption=caption)
        return f"IG photo posted: {os.path.basename(filepath)} (id={media.pk})" + (f" [client={client_name}]" if client_name else "")
    elif lower.endswith(".mp4"):
        media = cl.video_upload(path=filepath, caption=caption)
        return f"IG video posted: {os.path.basename(filepath)} (id={media.pk})" + (f" [client={client_name}]" if client_name else "")
    else:
        # Fallback try as video
        media = cl.video_upload(path=filepath, caption=caption)
        return f"IG media posted (fallback): {os.path.basename(filepath)} (id={media.pk})" + (f" [client={client_name}]" if client_name else "")



