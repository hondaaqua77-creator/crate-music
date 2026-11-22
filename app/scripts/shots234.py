#!/usr/bin/env python3
"""App Store screenshots #2-#4 (iPhone 6.9 / 6.5): all parts, PDF share, key card.
usage: shots234.py <shot1_dir with cap_after.png, keycard.png> <out_dir>"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
SANS_M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SANS_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
RED = (204, 47, 69); INK = (24, 24, 28); WHITE = (255, 255, 255); SUB = (255, 225, 228)
SIZES = {"6.9inch": (1320, 2868), "6.5inch": (1284, 2778)}


def f(p, s): return ImageFont.truetype(p, s)


def ctext(d, y, s, fnt, fill, W):
    d.text(((W - d.textlength(s, font=fnt)) / 2, y), s, font=fnt, fill=fill)


def shadow_paste(im, src, xy, r=0, blur=30, off=20, alpha=100):
    x, y = xy
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x, y + off, x + src.width, y + src.height + off), r, fill=(60, 0, 10, alpha))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    if r:
        m = Image.new("L", src.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, src.width - 1, src.height - 1), r, fill=255)
        im.paste(src.convert("RGBA"), (x, y), m)
    else:
        im.alpha_composite(src.convert("RGBA"), (x, y))


def base(W, H, l1, l2, sub):
    k = W / 1320; S = lambda v: int(v * k)
    im = Image.new("RGBA", (W, H), RED + (255,)); d = ImageDraw.Draw(im)
    ctext(d, S(170), l1, f(SANS_B, S(118)), WHITE, W)
    ctext(d, S(330), l2, f(SANS_B, S(130)), WHITE, W)
    ctext(d, S(530), sub, f(SANS_M, S(52)), SUB, W)
    return im, d, S


def shot_parts(W, H, cap):
    im, d, S = base(W, H, "伴奏も、全パート", "まとめて移調。", "歌・右手・左手の音符と調号を一度に書き換え")
    X0, Y0, X1, Y1 = 200, 350, 1080, 1150  # first system, 2 bars (2x capture)
    crop = cap.crop((X0, Y0, X1, Y1))
    mx = S(50); cw = W - 2 * mx; gut = S(150); top = S(150)
    sc = (cw - gut - S(30)) / crop.width; sh = int(crop.height * sc)
    card = Image.new("RGB", (cw, sh + top + S(50)), WHITE); cd = ImageDraw.Draw(card)
    card.paste(crop.resize((cw - gut - S(30), sh), Image.LANCZOS), (gut, top))
    bf = f(SANS_B, S(50)); s1 = "全パート  ♯3つ → ♯1つ"
    tw = cd.textlength(s1, font=bf); cd.rounded_rectangle((S(40), S(36), S(40) + tw + S(70), S(36) + S(84)), S(42), fill=RED)
    cd.text((S(75), S(44)), s1, font=bf, fill=WHITE)
    lf = f(SANS_B, S(46))
    for yt, nm in zip([400, 668, 898], ["歌", "右手", "左手"]):
        cy = top + int((yt - Y0 + 64) * sc)
        cd.text((S(30) + (gut - S(40) - cd.textlength(nm, font=lf)) / 2, cy - S(30)), nm, font=lf, fill=RED)
    y0 = S(680); shadow_paste(im, card, (mx, y0), r=S(48))
    d = ImageDraw.Draw(im); yb = y0 + card.height + S(110)
    tf = f(SANS_B, S(56)); items = ["合唱", "ピアノ伴奏", "弾き語り"]
    ws = [d.textlength(t, font=tf) + S(90) for t in items]; gap = S(26); x = (W - sum(ws) - gap * 2) / 2
    for t, w_ in zip(items, ws):
        d.rounded_rectangle((x, yb, x + w_, yb + S(130)), S(65), outline=WHITE, width=S(5))
        d.text((x + S(45), yb + S(30)), t, font=tf, fill=WHITE); x += w_ + gap
    return im.convert("RGB")


def shot_share(W, H, cap):
    im, d, S = base(W, H, "PDFで、そのまま", "仲間に送れる。", "LINE・メール・AirDropで共有")
    px, py, pw, ph = S(70), S(680), W - S(140), S(1500)
    panel = Image.new("RGB", (pw, ph), (236, 239, 244)); pd = ImageDraw.Draw(panel)
    pd.rectangle((0, 0, pw, S(150)), fill=WHITE)
    pd.text((S(50), S(42)), "‹", font=f(SANS_B, S(64)), fill=INK)
    pd.text((S(120), S(46)), "合唱団 練習連絡（24）", font=f(SANS_B, S(50)), fill=INK)
    # my file bubble
    page = cap.crop((40, 40, 2960, 2200)).convert("RGB")
    bw = int(pw * .66); bx = pw - bw - S(40); by = S(220)
    th = int(bw * .62); thumb = page.resize((bw - S(40), int(page.height * (bw - S(40)) / page.width)), Image.LANCZOS).crop((0, 0, bw - S(40), th))
    bub = Image.new("RGB", (bw, th + S(200)), WHITE); bd = ImageDraw.Draw(bub)
    bub.paste(thumb, (S(20), S(20)))
    bd.rounded_rectangle((S(20), th + S(40), S(110), th + S(130)), S(12), fill=RED)
    bd.text((S(30), th + S(58)), "PDF", font=f(SANS_B, S(36)), fill=WHITE)
    bd.text((S(130), th + S(40)), "Aus_meinen_Tränen_ト長調.pdf", font=f(SANS_M, S(36)), fill=INK)
    bd.text((S(130), th + S(92)), "1ページ・280KB", font=f(SANS_R, S(32)), fill=(120, 120, 128))
    m = Image.new("L", bub.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, bub.width - 1, bub.height - 1), S(36), fill=255)
    panel.paste(bub, (bx, by), m)
    y = by + bub.height + S(40)
    def bubble(text, right, y, col, tcol):
        fnt = f(SANS_M, S(44)); tw = pd.textlength(text, font=fnt); w_ = tw + S(80); h_ = S(110)
        x = pw - w_ - S(40) if right else S(150)
        if not right:
            pd.ellipse((S(30), y, S(120), y + S(90)), fill=(190, 196, 206)); pd.text((S(52), y + S(16)), "A", font=f(SANS_B, S(44)), fill=WHITE)
        pd.rounded_rectangle((x, y, x + w_, y + h_), S(55), fill=col); pd.text((x + S(40), y + S(24)), text, font=fnt, fill=tcol)
        return y + h_ + S(36)
    y = bubble("来週はこのキーで歌います！", True, y, RED, WHITE)
    y = bubble("高いところ、楽になりました！", False, y + S(20), WHITE, INK)
    y = bubble("アルトの分もありがとう", False, y, WHITE, INK)
    panel = panel.crop((0, 0, pw, min(ph, y + S(30))))
    shadow_paste(im, panel, (px, py), r=S(56))
    d = ImageDraw.Draw(im); yb = py + panel.height + S(110)
    tf = f(SANS_B, S(56)); items = ["LINE", "メール", "AirDrop", "印刷"]
    ws = [d.textlength(t, font=tf) + S(80) for t in items]; gap = S(22); x = (W - sum(ws) - gap * 3) / 2
    for t, w_ in zip(items, ws):
        d.rounded_rectangle((x, yb, x + w_, yb + S(130)), S(65), outline=WHITE, width=S(5))
        d.text((x + S(40), yb + S(30)), t, font=tf, fill=WHITE); x += w_ + gap
    return im.convert("RGB")


def shot_card(W, H, card):
    im, d, S = base(W, H, "移調カードで、", "仲間に紹介。", "歌いやすくしたキーを、画像でシェア")
    cw = W - S(160); c = card.resize((cw, int(card.height * cw / card.width)), Image.LANCZOS)
    shadow_paste(im, c, ((W - cw) // 2, S(700)), r=S(40), blur=40, off=30, alpha=130)
    d = ImageDraw.Draw(im); yb = S(700) + c.height + S(110)
    tf = f(SANS_B, S(54)); s = "送ると、24時間 広告なし（1日1回）"
    tw = d.textlength(s, font=tf); d.rounded_rectangle(((W - tw) / 2 - S(50), yb, (W + tw) / 2 + S(50), yb + S(130)), S(65), fill=WHITE)
    d.text(((W - tw) / 2, yb + S(30)), s, font=tf, fill=RED)
    return im.convert("RGB")


def main():
    src, out = sys.argv[1:3]
    cap = Image.open(os.path.join(src, "cap_after.png")).convert("RGB")
    card = Image.open(os.path.join(src, "keycard.png")).convert("RGB")
    for tag, (W, H) in SIZES.items():
        for name, fn, arg in (("2_parts", shot_parts, cap), ("3_share", shot_share, cap), ("4_card", shot_card, card)):
            p = os.path.join(out, f"phone_{tag}_{name}.png"); fn(W, H, arg).save(p, optimize=True); print("wrote", p)


if __name__ == "__main__":
    main()
