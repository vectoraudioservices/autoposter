import os
import re
from datetime import datetime

# pull useful words from the file name to make hashtags
def infer_keywords_from_filename(path: str):
    base = os.path.splitext(os.path.basename(path))[0]
    parts = re.split(r"[-_ ]+", base)
    ignore = {"final", "export", "edit", "clip", "image", "video", "vid", "img"}
    words = [p.lower() for p in parts if p and p.lower() not in ignore]
    return words[:6]  # cap to 6 tags

def make_caption(filepath: str) -> str:
    kws = infer_keywords_from_filename(filepath)
    tags = " ".join(f"#{w}" for w in kws if len(w) > 1)
    date_tag = datetime.now().strftime("%b %d")
    caption = (
        f"🔥 New drop • {date_tag}\n"
        f"{tags}\n"
        f"Follow @VectorManagement for daily drops. 🚀"
    )
    return caption
