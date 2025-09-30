from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("db", str(ROOT/"scripts"/"db.py"))
db = importlib.util.module_from_spec(spec); spec.loader.exec_module(db)  # type: ignore

db.init_db()
p = ROOT / "content/Luchiano/feed/test_photo.jpg"
p.parent.mkdir(parents=True, exist_ok=True)
if not p.exists():
    p.write_bytes(b"x")
jid = db.add_job("Luchiano", str(p), content_type="feed", caption="(smoke)", extras={"source":"smoke"})
print("INSERTED job#", jid)
