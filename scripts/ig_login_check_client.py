import os, sys, json, logging
from pathlib import Path
from instagrapi import Client

CONFIG_DIR = Path("config")
CLIENTS_DIR = CONFIG_DIR / "clients"
SESS_DIR = CONFIG_DIR / "sessions"
SESS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def load_creds(client_name: str):
    cfg_path = CLIENTS_DIR / client_name / "client.json"
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    u, p = data.get("IG_USERNAME"), data.get("IG_PASSWORD")
    if not (u and p):
        raise RuntimeError(f"Missing IG_USERNAME/IG_PASSWORD in {cfg_path}")
    return u, p

def main():
    if len(sys.argv) < 2:
        print("Usage: ig_login_check_client.py <ClientName>"); sys.exit(2)
    client = sys.argv[1]
    user, pw = load_creds(client)

    cl = Client()


    # Fresh login (don’t load any old session first)
    try:
        twofa = os.getenv("IG_2FA_CODE")
        if twofa:
            logging.info("Logging in with 2FA code present.")
            cl.login(user, pw, verification_code=twofa)
        else:
            logging.info("Logging in without 2FA.")
            cl.login(user, pw)
        # Save a clean session for future runs
        sess = SESS_DIR / f"{client}.json"
        cl.dump_settings(str(sess))
        me = cl.account_info()  # private sanity check
        logging.info("✅ Login OK: %s (pk=%s)", getattr(me, "username", "<unknown>"), getattr(me, "pk", "n/a"))
        logging.info("Saved session: %s", sess)
        sys.exit(0)
    except Exception as e:
        logging.exception("❌ Login failed: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
