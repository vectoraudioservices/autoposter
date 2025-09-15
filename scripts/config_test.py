import os
import json
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT, "config", "schedule.json")

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)

def get_next_post_time(best_hours):
    now = datetime.now()
    today_slots = [now.replace(hour=h, minute=0, second=0, microsecond=0) for h in best_hours]
    for slot in today_slots:
        if slot > now:
            return slot
    # if no slots left today, pick the first tomorrow
    return (now + timedelta(days=1)).replace(hour=best_hours[0], minute=0, second=0, microsecond=0)

if __name__ == "__main__":
    cfg = load_config()
    hours = cfg["best_times"]["default_hours_24"]
    nxt = get_next_post_time(hours)
    print("Best posting hours:", hours)
    print("Now:", datetime.now())
    print("Next scheduled slot:", nxt)

