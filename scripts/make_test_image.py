import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
os.makedirs(CONTENT, exist_ok=True)

def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = os.path.join(CONTENT, "ig_live_smoke_test.jpg")

    img = Image.new("RGB", (900, 900), (32, 32, 32))
    draw = ImageDraw.Draw(img)
    text = f"Vector Autoposter\nIG live smoke test\n{ts}"
    try:
        # default bitmap font (portable)
        draw.multiline_text((60, 380), text, fill=(240, 240, 240), spacing=8, align="left")
    except Exception:
        pass

    img.save(path, "JPEG", quality=85)
    print(path)

if __name__ == "__main__":
    main()
