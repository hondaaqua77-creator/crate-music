#!/usr/bin/env python3
"""Google Play listing graphics from the iOS store assets.
Outputs app/store/play/: icon-512.png, feature-1024x500.png, phone/*.png (1080x2160, 2:1), tablet10/*.png (1536x2048)
"""
import glob, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
STORE = os.path.join(ROOT, "app", "store")
OUT = os.path.join(STORE, "play")
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
SANS_M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
RED, DEEP, GOLD = (210, 52, 74), (120, 26, 40), (232, 200, 140)


def edge_color(im):
    px = [im.getpixel((x, y)) for x in (2, im.width - 3) for y in range(0, im.height, max(1, im.height // 40))]
    return tuple(sorted(c[i] for c in px)[len(px) // 2] for i in range(3))


def fit_canvas(src, size):
    im = Image.open(src).convert("RGB"); W, H = size
    s = min(W / im.width, H / im.height)
    r = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    c = Image.new("RGB", size, edge_color(im)); c.paste(r, ((W - r.width) // 2, (H - r.height) // 2))
    return c


def feature():
    W, H = 1024, 500
    im = Image.new("RGB", (W, H), DEEP)
    g = Image.new("L", (W, H), 0); ImageDraw.Draw(g).ellipse((-200, -150, 700, 650), fill=170)
    im = Image.composite(Image.new("RGB", (W, H), RED), im, g.filter(ImageFilter.GaussianBlur(160)))
    d = ImageDraw.Draw(im)
    icon = Image.open(os.path.join(ROOT, "icons", "icon-1024.png")).convert("RGB").resize((150, 150), Image.LANCZOS)
    m = Image.new("L", (150, 150), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 149, 149), 34, fill=255)
    im.paste(icon, (64, 70), m)
    x = 64; f1 = ImageFont.truetype(SANS_B, 58); f2 = ImageFont.truetype(SANS_M, 30); fw = ImageFont.truetype(SANS_M, 40)
    cx = 236
    for ch in "CRATE":
        d.text((cx, 112), ch, font=fw, fill="white"); cx += d.textlength(ch, font=fw) + 10
    d.text((x, 260), "楽譜を、撮るだけで", font=f1, fill="white")
    d.text((x, 335), "好きなキーに。", font=f1, fill="white")
    d.text((x, 420), "音符も調号も書き直し → PDFでLINEへ", font=f2, fill=GOLD)
    # phone screenshot on the right
    shot = sorted(glob.glob(os.path.join(STORE, "screenshots", "phone_6.5inch_1_*.png")))[0]
    s = Image.open(shot).convert("RGB"); sw = 250; s = s.resize((sw, int(s.height * sw / s.width)), Image.LANCZOS)
    s = s.crop((0, 0, sw, 460))
    sm = Image.new("L", s.size, 0); ImageDraw.Draw(sm).rounded_rectangle((0, 0, sw - 1, 520), 30, fill=255)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((730, 70, 730 + sw, 540), 30, fill=(0, 0, 0, 150))
    im = Image.alpha_composite(im.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(20))).convert("RGB")
    im.paste(s, (720, 50), sm)
    im.save(os.path.join(OUT, "feature-1024x500.png"))


def main():
    os.makedirs(os.path.join(OUT, "phone"), exist_ok=True); os.makedirs(os.path.join(OUT, "tablet10"), exist_ok=True)
    Image.open(os.path.join(ROOT, "icons", "icon-1024.png")).convert("RGB").resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "icon-512.png"))
    for f in sorted(glob.glob(os.path.join(STORE, "screenshots", "phone_6.5inch_*.png"))):
        fit_canvas(f, (1080, 2160)).save(os.path.join(OUT, "phone", os.path.basename(f).replace("phone_6.5inch_", "")))
    for f in sorted(glob.glob(os.path.join(STORE, "screenshots", "pad_13inch_*.png"))):
        fit_canvas(f, (1536, 2048)).save(os.path.join(OUT, "tablet10", os.path.basename(f).replace("pad_13inch_", "")))
    feature()
    print("ok")


if __name__ == "__main__":
    main()
