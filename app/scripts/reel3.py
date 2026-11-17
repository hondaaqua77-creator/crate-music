#!/usr/bin/env python3
"""Reel 3: real app screen demo with a before/after hook in the first frame.
usage: reel3.py <frames_dir> <music.mp3> <out.mp4>
frames_dir comes from reel-shoot.py (fr_*.png at 1170x2532).
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
RED, DEEP, WHITE, INK = (210, 52, 74), (120, 26, 40), (255, 255, 255), (20, 22, 27)
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
MED = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
CROP = (40, 280, 760, 560)  # first system incl. key signature, in 1170x2532 frames


def bg():
    im = Image.new("RGB", (W, H), DEEP)
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse((-200, 300, W + 200, H + 300), fill=140)
    g = g.filter(ImageFilter.GaussianBlur(260))
    return Image.composite(Image.new("RGB", (W, H), RED), im, g)


def caption(d, lines, y=110, size=86, sub=None):
    f = ImageFont.truetype(BOLD, size)
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text(((W - w) / 2, y), ln, font=f, fill=WHITE)
        y += int(size * 1.25)
    if sub:
        fs = ImageFont.truetype(MED, 42)
        w = d.textlength(sub, font=fs)
        d.text(((W - w) / 2, y + 6), sub, font=fs, fill=(255, 225, 225))
    return y


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    out = im.convert("RGBA"); out.putalpha(m); return out


def paste_shadow(base, im, x, y, r=36):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x, y + 14, x + im.width, y + im.height + 14), r, fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(24))
    base = Image.alpha_composite(base.convert("RGBA"), sh)
    ri = rounded(im, r)
    base.paste(ri, (x, y), ri)
    return base.convert("RGB")


def phone_frame(src, lines, sub=None):
    im = bg(); d = ImageDraw.Draw(im)
    y = caption(d, lines, sub=sub)
    ph = Image.open(src).convert("RGB")
    pw = 880; phh = int(ph.height * pw / ph.width)
    ph = ph.resize((pw, phh), Image.LANCZOS)
    top = max(y + 70, 400)
    ph = ph.crop((0, 0, pw, min(phh, H - top + 60)))
    return paste_shadow(im, ph, (W - pw) // 2, top)


def hook_frame(before, after):
    im = bg(); d = ImageDraw.Draw(im)
    caption(d, ["楽譜のキー、", "ボタン2回で変わる。"], y=100, size=92)
    a = Image.open(before).convert("RGB").crop(CROP); b = Image.open(after).convert("RGB").crop(CROP)
    cw = 960; ch = int(a.height * cw / a.width)
    a = a.resize((cw, ch), Image.LANCZOS); b = b.resize((cw, ch), Image.LANCZOS)
    fl = ImageFont.truetype(BOLD, 44)
    x = (W - cw) // 2
    y1 = 470
    d.rounded_rectangle((x, y1 - 70, x + 300, y1 - 10), 30, fill=WHITE); d.text((x + 30, y1 - 66), "前：イ長調", font=fl, fill=INK)
    im = paste_shadow(im, a, x, y1, 24)
    d = ImageDraw.Draw(im)
    fa = ImageFont.truetype(BOLD, 90)
    d.text(((W - d.textlength("↓", font=fa)) / 2, y1 + ch + 10), "↓", font=fa, fill=WHITE)
    y2 = y1 + ch + 190
    d.rounded_rectangle((x, y2 - 70, x + 420, y2 - 10), 30, fill=(255, 220, 120)); d.text((x + 30, y2 - 66), "後：ロ長調（＋2）", font=fl, fill=INK)
    im = paste_shadow(im, b, x, y2, 24)
    return im


def end_card():
    im = bg(); d = ImageDraw.Draw(im)
    icon = os.path.join(ROOT, "icons", "icon-1024.png")
    if os.path.exists(icon):
        ic = Image.open(icon).convert("RGB").resize((260, 260), Image.LANCZOS)
        im = paste_shadow(im, ic, (W - 260) // 2, 560, 58); d = ImageDraw.Draw(im)
    fw = ImageFont.truetype(MED, 118)
    t = "CRATE"; tr = 22
    w = sum(d.textlength(c, font=fw) for c in t) + tr * (len(t) - 1); x = (W - w) / 2
    for c in t:
        d.text((x, 870), c, font=fw, fill=WHITE); x += d.textlength(c, font=fw) + tr
    caption(d, ["楽譜をかんたん移調"], y=1030, size=60)
    fp = ImageFont.truetype(MED, 42)
    cta = "App Storeで「CRATE 移調」と検索"
    cw = d.textlength(cta, font=fp)
    px = (W - cw) / 2 - 50
    d.rounded_rectangle((px, 1200, px + cw + 100, 1310), 55, fill=WHITE)
    d.text(((W - cw) / 2, 1228), cta, font=fp, fill=DEEP)
    fs = ImageFont.truetype(MED, 38)
    t2 = "無料 ・ iPhone ・ iPad"
    d.text(((W - d.textlength(t2, font=fs)) / 2, 1360), t2, font=fs, fill=(255, 225, 225))
    return im


def main():
    fr, music, out = sys.argv[1:4]
    p = lambda n: os.path.join(fr, n)
    shots = [
        (hook_frame(p("fr_b_score.png"), p("fr_f_done.png")), 2.4),
        (phone_frame(p("fr_b_score.png"), ["印刷した楽譜を", "写真で読み込んで"]), 1.5),
        (phone_frame(p("fr_c_tp.png"), ["「移調」→ ♯を押す"]), 1.3),
        (phone_frame(p("fr_e_s200.png"), ["音符も調号も、", "自動で書き直し"]), 0.5),
        (phone_frame(p("fr_e_s202.png"), ["音符も調号も、", "自動で書き直し"]), 0.5),
        (phone_frame(p("fr_f_done.png"), ["音符も調号も、", "自動で書き直し"], sub="イ長調 → ロ長調（215音）"), 1.6),
        (phone_frame(p("fr_g_pdf.png"), ["PDFで保存して、", "LINEで送れる"]), 2.0),
        (end_card(), 3.2),
    ]
    tmp = tempfile.mkdtemp(); lst = os.path.join(tmp, "l.txt")
    with open(lst, "w") as f:
        for i, (im, dur) in enumerate(shots):
            fn = os.path.join(tmp, f"s{i}.png"); im.save(fn)
            f.write(f"file '{fn}'\nduration {dur}\n")
        f.write(f"file '{fn}'\n")
    total = sum(d for _, d in shots)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", music,
                    "-filter_complex", f"[0:v]fps=30,scale={W}:{H},format=yuv420p[v];[1:a]atrim=0:{total},asetpts=PTS-STARTPTS,afade=t=out:st={total-1.5}:d=1.5,loudnorm=I=-16:TP=-1.5:LRA=9[a]",
                    "-map", "[v]", "-map", "[a]", "-t", str(total), "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", out], check=True)
    shots[0][0].save(os.path.splitext(out)[0] + "_cover.jpg", quality=92)
    print("wrote", out, total, "s")


if __name__ == "__main__":
    main()
