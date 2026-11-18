#!/usr/bin/env python3
"""Stylish covers for reel 3 (3 variants). Key content kept inside the 3:4 grid-safe centre (y 240..1680).
usage: reel3cover.py <covers_dir>
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 1080, 1920
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
SANS_M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
SERIF_L = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc"
RED, GOLD, WHITE = (210, 52, 74), (232, 200, 140), (255, 255, 255)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")


def sp(d, x, y, s, f, fill, tr):
    for c in s:
        d.text((x, y), c, font=f, fill=fill); x += d.textlength(c, font=f) + tr


def sw(d, s, f, tr):
    return sum(d.textlength(c, font=f) for c in s) + tr * (len(s) - 1)


def grade(im, dark=0.35):
    im = ImageEnhance.Contrast(im).enhance(1.12)
    g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)
    for y in range(H):  # top & bottom darkening for type
        a = max(0, 1 - y / 760) ** 1.4 * 235 + max(0, (y - 1150) / 770) ** 1.3 * 245
        gd.line((0, y, W, y), fill=int(min(255, a)))
    im = Image.composite(Image.new("RGB", (W, H), (8, 6, 8)), im, g)
    return Image.blend(im, Image.new("RGB", (W, H), (0, 0, 0)), dark)


def shadow_text(base, fn):
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(ImageDraw.Draw(sh), (0, 0, 0, 190))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    fn(ImageDraw.Draw(base), None)


def icon_small(base, x, y, s=92):
    p = os.path.join(ROOT, "icons", "icon-1024.png")
    if not os.path.exists(p): return
    ic = Image.open(p).convert("RGB").resize((s, s), Image.LANCZOS)
    m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, s - 1, s - 1), int(s * .23), fill=255)
    base.paste(ic, (x, y), m)


def brand_row(base, y):
    d = ImageDraw.Draw(base); f = ImageFont.truetype(SANS_M, 46)
    t = "CRATE"; tw = sw(d, t, f, 14); total = 92 + 26 + tw; x = (W - total) / 2
    icon_small(base, int(x), y - 18)
    sp(d, x + 118, y, t, f, WHITE, 14)


# A: bold editorial — huge serif over red stage piano
def cover_a(bg):
    im = grade(Image.open(bg).convert("RGB"), 0.15).convert("RGBA")
    def txt(d, sc):
        f1 = ImageFont.truetype(SERIF_B, 168); f2 = ImageFont.truetype(SERIF_B, 168)
        for s, y, f in (("そのキー、", 350, f1), ("2タップ。", 560, f2)):
            x = (W - sw(d, s, f, 4)) / 2; sp(d, x + (0 if sc is None else 0), y + (8 if sc else 0), s, f, sc or WHITE, 4)
    shadow_text(im, txt)
    d = ImageDraw.Draw(im)
    ft = ImageFont.truetype(SANS_M, 34); t = "TRANSPOSE  ANY  SCORE"
    d.rectangle((W / 2 - 70, 312, W / 2 + 70, 315), fill=GOLD)
    sp(d, (W - sw(d, t, ft, 12)) / 2, 258, t, ft, GOLD, 12)
    # key change pill
    fp = ImageFont.truetype(SANS_B, 52); a, b = "イ長調", "ロ長調"
    aw, bw = d.textlength(a, font=fp), d.textlength(b, font=fp); arr = 110
    tot = aw + bw + arr + 120; x0 = (W - tot) / 2; y0 = 1360
    d.rounded_rectangle((x0, y0, x0 + tot, y0 + 110), 55, fill=(255, 255, 255, 235))
    d.text((x0 + 50, y0 + 22), a, font=fp, fill=(30, 30, 34))
    ax = x0 + 50 + aw + 20; d.line((ax, y0 + 55, ax + arr - 40, y0 + 55), fill=RED, width=6)
    d.polygon([(ax + arr - 40, y0 + 40), (ax + arr - 14, y0 + 55), (ax + arr - 40, y0 + 70)], fill=RED)
    d.text((ax + arr, y0 + 22), b, font=fp, fill=RED)
    brand_row(im, 1530)
    return im.convert("RGB")


# B: split before/after card on deep red, magazine layout
def cover_b(bg, fr):
    im = grade(Image.open(bg).convert("RGB"), 0.25).convert("RGBA")
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(SANS_B, 140)
    def txt(dd, sc):
        for s, y, col in (("楽譜のキー、", 300, WHITE), ("一瞬で変える。", 480, WHITE)):
            sp(dd, (W - sw(dd, s, f, 0)) / 2, y + (8 if sc else 0), s, f, sc or col, 0)
    # red highlight bar under 2nd line
    bw = sw(d, "一瞬で変える。", f, 0); x = (W - bw) / 2
    d.rectangle((x - 20, 520, x + bw + 20, 648), fill=RED + (240,))
    shadow_text(im, txt)
    crop = (40, 280, 760, 560)
    a = Image.open(os.path.join(fr, "fr_b_score.png")).convert("RGB").crop(crop)
    b = Image.open(os.path.join(fr, "fr_f_done.png")).convert("RGB").crop(crop)
    cw = 860; ch = int(a.height * cw / a.width)
    for img, y, lab, col in ((a, 800, "BEFORE", WHITE), (b, 800 + ch + 90, "AFTER", GOLD)):
        img = img.resize((cw, ch), Image.LANCZOS)
        m = Image.new("L", img.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, cw - 1, ch - 1), 22, fill=255)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle(((W - cw) // 2, y + 16, (W + cw) // 2, y + ch + 16), 22, fill=(0, 0, 0, 170))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))
        im.paste(img, ((W - cw) // 2, y), m)
        d = ImageDraw.Draw(im); fl = ImageFont.truetype(SANS_B, 34)
        sp(d, (W - cw) / 2, y - 50, lab, fl, col, 10)
    brand_row(im, 1600)
    return im.convert("RGB")


# C: minimal luxe — notes macro, thin type, lots of air
def cover_c(bg):
    im = grade(Image.open(bg).convert("RGB"), 0.2).convert("RGBA")
    d = ImageDraw.Draw(im)
    ft = ImageFont.truetype(SANS_M, 32); t = "CRATE  ·  TRANSPOSE"
    sp(d, (W - sw(d, t, ft, 12)) / 2, 300, t, ft, GOLD, 12)
    f = ImageFont.truetype(SERIF_B, 150)
    def txt(dd, sc):
        for s, y in (("歌いやすい", 380), ("キーへ。", 560)):
            sp(dd, (W - sw(dd, s, f, 6)) / 2, y + (8 if sc else 0), s, f, sc or WHITE, 6)
    shadow_text(im, txt)
    d = ImageDraw.Draw(im); fs = ImageFont.truetype(SERIF_L, 50)
    s = "写真1枚で、楽譜を移調。"
    d.text(((W - d.textlength(s, font=fs)) / 2, 1400), s, font=fs, fill=(240, 230, 215))
    d.rectangle((W / 2 - 40, 1500, W / 2 + 40, 1502), fill=GOLD)
    brand_row(im, 1560)
    return im.convert("RGB")


def main():
    cd = sys.argv[1]; fr = sys.argv[2]
    out = {"A": cover_a(os.path.join(cd, "bg_c6_1.5.png")),
           "B": cover_b(os.path.join(cd, "bg_c2_0.5.png"), fr),
           "C": cover_c(os.path.join(cd, "bg_c2_2.6.png"))}
    tiles = []
    for k, im in out.items():
        im.save(os.path.join(cd, f"cover_{k}.jpg"), quality=93)
        t = im.resize((360, 640)); dd = ImageDraw.Draw(t)
        dd.rectangle((0, 80, 359, 559), outline=(255, 255, 0), width=2)  # 3:4 grid crop guide
        dd.text((12, 10), k, font=ImageFont.truetype(SANS_B, 40), fill=(255, 255, 0)); tiles.append(t)
    sheet = Image.new("RGB", (360 * 3 + 20, 640), (40, 40, 40))
    for i, t in enumerate(tiles): sheet.paste(t, (i * 370, 0))
    sheet.save(os.path.join(cd, "sheet.png"))


if __name__ == "__main__":
    main()
