#!/usr/bin/env python3
"""App Store screenshot #1: before/after transposition, readable at search-result thumbnail size.
usage: shot1.py <cap_before.png> <cap_after.png> <out_dir>
cap_*.png = 2x captures of the score stage (sample score, original / -2 semitones)."""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
SANS_M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
RED = (204, 47, 69); INK = (24, 24, 28); WHITE = (255, 255, 255)
CROP = (210, 364, 1060, 610)  # voice staff, first 2 bars + lyrics (2x coords)
KEYSIG = (106, 22, 214, 176)  # key-signature area inside CROP (for the highlight ring)


def f(p, s): return ImageFont.truetype(p, s)


def ctext(d, y, s, fnt, fill, W):
    d.text(((W - d.textlength(s, font=fnt)) / 2, y), s, font=fnt, fill=fill)


def card(im, x, y, w, h, r=48):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x, y + 18, x + w, y + h + 18), r, fill=(80, 0, 15, 90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(28)))
    ImageDraw.Draw(im).rounded_rectangle((x, y, x + w, y + h), r, fill=WHITE + (255,))


def render(W, H, before, after):
    k = W / 1320
    im = Image.new("RGBA", (W, H), RED + (255,)); d = ImageDraw.Draw(im)
    S = lambda v: int(v * k)
    ctext(d, S(170), "高くて歌えない曲を、", f(SANS_B, S(118)), WHITE, W)
    ctext(d, S(330), "歌えるキーに。", f(SANS_B, S(150)), WHITE, W)
    ctext(d, S(540), "楽譜の写真から、音符も調号も書き換え", f(SANS_M, S(52)), (255, 225, 228), W)
    mx = S(60); cw = W - 2 * mx
    sw = cw - S(40); sc = sw / before.width; shh = int(before.height * sc)
    ch = shh + S(190)
    y1 = S(680); y2 = y1 + ch + S(250)
    for idx, (img, tag, key, y) in enumerate(((before, "元の楽譜", "イ長調", y1), (after, "CRATEで移調", "ト長調", y2))):
        card(im, mx, y, cw, ch)
        d = ImageDraw.Draw(im)
        tf = f(SANS_B, S(52)); pad = S(28)
        tw = d.textlength(tag, font=tf)
        col = (150, 150, 158) if idx == 0 else RED
        d.rounded_rectangle((mx + S(40), y + S(44), mx + S(40) + tw + pad * 2, y + S(44) + S(88)), S(44), fill=col)
        d.text((mx + S(40) + pad, y + S(50)), tag, font=tf, fill=WHITE)
        d.text((mx + S(40) + tw + pad * 2 + S(30), y + S(50)), key, font=f(SANS_B, S(64)), fill=INK)
        ox, oy = mx + S(20), y + S(170)
        im.alpha_composite(img.resize((sw, shh), Image.LANCZOS).convert("RGBA"), (ox, oy))
        kx0, ky0, kx1, ky1 = [v * sc for v in KEYSIG]
        d.rounded_rectangle((ox + kx0, oy + ky0, ox + kx1, oy + ky1), S(36), outline=RED if idx else (150, 150, 158), width=S(8))
    d = ImageDraw.Draw(im)
    ay = y1 + ch + S(40); r = S(85)
    lf = f(SANS_B, S(58)); s2 = "2回タップで、全音下げ"
    tw2 = d.textlength(s2, font=lf); gx = (W - (2 * r + S(36) + tw2)) / 2
    d.ellipse((gx, ay, gx + 2 * r, ay + 2 * r), fill=WHITE)
    af = f(SANS_B, S(64)); s = "♭♭"
    d.text((gx + r - d.textlength(s, font=af) / 2, ay + r - S(46)), s, font=af, fill=RED)
    d.text((gx + 2 * r + S(36), ay + r - S(42)), s2, font=lf, fill=WHITE)
    by = H - S(360)
    items = ["撮るだけ", "全パート一括", "PDFで共有"]
    bf = f(SANS_B, S(52)); gap = S(28)
    ws = [d.textlength(t, font=bf) + S(80) for t in items]; x = (W - sum(ws) - gap * 2) / 2
    for t, w_ in zip(items, ws):
        d.rounded_rectangle((x, by, x + w_, by + S(120)), S(60), outline=WHITE, width=S(5))
        d.text((x + S(40), by + S(28)), t, font=bf, fill=WHITE); x += w_ + gap
    return im.convert("RGB")


def main():
    b, a, out = sys.argv[1:4]
    before = Image.open(b).convert("RGB").crop(CROP); after = Image.open(a).convert("RGB").crop(CROP)
    for name, (W, H) in {"phone_6.9inch_1_transpose.png": (1320, 2868), "phone_6.5inch_1_transpose.png": (1284, 2778)}.items():
        render(W, H, before, after).save(os.path.join(out, name), optimize=True)
        print("wrote", name)


if __name__ == "__main__":
    main()
