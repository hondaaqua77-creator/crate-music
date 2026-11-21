#!/usr/bin/env python3
"""Reel 3 (dynamic CM): beat-synced fast cuts, kinetic type, zoom punches, white flashes.
usage: reel3dyn.py <clips_dir c1..c6.mp4> <frames_dir fr_*.png> <music.mp3> <out.mp4> [bpm]
Renders every frame in Python (PIL) over decoded clip frames -> pipes raw video to ffmpeg.
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
SANS_M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
RED, GOLD, WHITE = (210, 52, 74), (232, 200, 140), (255, 255, 255)
CROP = (40, 280, 760, 560)


def ease(t):  # easeOutCubic
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3


def ease_back(t, s=1.9):
    t = max(0.0, min(1.0, t)) - 1; return t * t * ((s + 1) * t + s) + 1


class Clip:
    """decodes to a raw file on disk and reads frames on demand (keeps memory low)"""
    def __init__(self, path, ss=0.0, speed=1.0, max_frames=150):
        import tempfile, atexit
        self.raw = tempfile.mktemp(suffix=".rgb")
        atexit.register(lambda p=self.raw: os.path.exists(p) and os.remove(p))  # never leave ~1GB caches behind
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", path, "-vf",
                        f"setpts=PTS/{speed},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                        "eq=contrast=1.1:saturation=1.05,vignette=PI/4.5",
                        "-frames:v", str(max_frames), "-f", "rawvideo", "-pix_fmt", "rgb24", self.raw], check=True)
        self.fs = W * H * 3
        self.n = os.path.getsize(self.raw) // self.fs

    def at(self, i):
        i = min(i, self.n - 1)
        with open(self.raw, "rb") as f:
            f.seek(i * self.fs); return Image.frombytes("RGB", (W, H), f.read(self.fs))


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(d, s, f, tr=0):
    return sum(d.textlength(c, font=f) for c in s) + tr * (len(s) - 1)


def draw_spaced(d, x, y, s, f, fill, tr=0):
    for c in s:
        d.text((x, y), c, font=f, fill=fill); x += d.textlength(c, font=f) + tr


def kinetic(base, lines, t, y, size=118, color=WHITE, stagger=0.06, shadow=True, hl=None):
    """each line slides up from a mask + fades in; hl = (line_index, color) for a highlight bar"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = font(SANS_B, size)
    yy = y
    for i, ln in enumerate(lines):
        p = ease((t - i * stagger) / 0.28)
        if p <= 0: yy += int(size * 1.22); continue
        tw = text_w(d, ln, f, 2); x = (W - tw) / 2
        off = (1 - p) * size * 0.9
        if hl and hl[0] == i:
            bw = tw * ease((t - i * stagger - 0.12) / 0.3)
            d.rectangle((x - 18, yy + size * 0.18, x - 18 + bw + 36, yy + size * 1.12), fill=hl[1] + (235,))
        line = Image.new("RGBA", (W, int(size * 1.4)), (0, 0, 0, 0)); ld = ImageDraw.Draw(line)
        draw_spaced(ld, x, off, ln, f, color + (int(255 * p),), 2)
        if shadow:
            sh = Image.new("RGBA", line.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
            draw_spaced(sd, x, off + 6, ln, f, (0, 0, 0, int(170 * p)), 2)
            lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (0, yy))
        lay.alpha_composite(line, (0, yy))
        yy += int(size * 1.22)
    base.alpha_composite(lay)


def tag(base, s, t, y, color=GOLD):
    d = ImageDraw.Draw(base); f = font(SANS_M, 32); p = ease(t / 0.3)
    tw = text_w(d, s, f, 10); x = (W - tw) / 2
    d.rectangle((W / 2 - 60 * p, y - 22, W / 2 + 60 * p, y - 19), fill=color + (255,))
    draw_spaced(d, x, y, s, f, color + (int(255 * p),), 10)


def punch(img, t, amt=0.08, dur=0.18):
    """zoom-punch at cut start: scale from 1+amt down to 1"""
    z = 1 + amt * (1 - ease(t / dur))
    if z <= 1.001: return img
    w, h = int(W * z), int(H * z)
    return img.resize((w, h), Image.BILINEAR).crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))


def slow_zoom(img, t, rate=0.03):
    z = 1 + rate * t; w, h = int(W * z), int(H * z)
    return img.resize((w, h), Image.BILINEAR).crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))


def flash(img, t, dur=0.12, strength=0.85):
    if t >= dur: return img
    a = strength * (1 - t / dur)
    return Image.blend(img.convert("RGB"), Image.new("RGB", (W, H), WHITE), a).convert("RGBA")


def darken(img, a=0.35):
    return Image.blend(img.convert("RGB"), Image.new("RGB", (W, H), (0, 0, 0)), a).convert("RGBA")


def red_bg():
    im = Image.new("RGB", (W, H), (120, 26, 40))
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse((-200, 400, W + 200, H + 200), fill=150)
    return Image.composite(Image.new("RGB", (W, H), RED), im, g.filter(ImageFilter.GaussianBlur(260))).convert("RGBA")


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    o = im.convert("RGBA"); o.putalpha(m); return o


def phone_img(src, width=700):
    sc = Image.open(src).convert("RGB"); h = int(sc.height * width / sc.width)
    sc = sc.resize((width, h), Image.LANCZOS); b = 16
    body = Image.new("RGBA", (width + 2 * b, h + 2 * b), (0, 0, 0, 0))
    ImageDraw.Draw(body).rounded_rectangle((0, 0, body.width - 1, body.height - 1), 90, fill=(20, 20, 24, 255))
    s = rounded(sc, 76); body.paste(s, (b, b), s)
    return body


def place_phone(base, ph, t, y0=640, tilt=True):
    """phone flies up with overshoot and a little rotation"""
    p = ease_back(t / 0.42)
    y = y0 + (1 - p) * 900
    rot = (1 - ease(t / 0.5)) * (-9 if tilt else 0)
    img = ph.rotate(rot, resample=Image.BICUBIC, expand=True) if abs(rot) > 0.1 else ph
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = (W - img.width) // 2
    ImageDraw.Draw(sh).rounded_rectangle((x + 20, int(y) + 50, x + img.width - 20, int(y) + img.height + 30), 90, fill=(0, 0, 0, 170))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)))
    base.alpha_composite(img, (x, int(y)))


def main():
    cd, fr, music, out = sys.argv[1:5]
    bpm = float(sys.argv[5]) if len(sys.argv) > 5 else 124.0
    beat = 60.0 / bpm
    C = lambda n, **k: Clip(os.path.join(cd, f"c{n}.mp4"), **k)
    clips = {1: C(5, ss=2.6), 2: C(2), 3: C(6, ss=2.2), 4: C(4), 5: C(5), 6: C(6, ss=0.3), 7: C(2, ss=2.4), 8: C(2, ss=1.0)}
    ph_tp = phone_img(os.path.join(fr, "fr_c_tp.png"))
    ph_done = phone_img(os.path.join(fr, "fr_f_done.png"))
    ph_pdf = phone_img(os.path.join(fr, "fr_g_pdf.png"))
    before = Image.open(os.path.join(fr, "fr_b_score.png")).convert("RGB").crop(CROP)
    after = Image.open(os.path.join(fr, "fr_f_done.png")).convert("RGB").crop(CROP)
    cw = 960; ch = int(before.height * cw / before.width)
    before = rounded(before.resize((cw, ch), Image.LANCZOS), 20); after = rounded(after.resize((cw, ch), Image.LANCZOS), 20)
    icon = os.path.join(ROOT, "icons", "icon-1024.png")
    icon = rounded(Image.open(icon).convert("RGB").resize((280, 280), Image.LANCZOS), 62) if os.path.exists(icon) else None

    B = lambda n: n * beat  # beats -> seconds
    # (start_beat, len_beats, renderer)
    def hook(t, i):
        im = slow_zoom(clips[2].at(i), t, 0.04).convert("RGBA"); im = darken(im, 0.45)
        # score card: before, then snaps to after on beat 4
        swap = t >= B(4)
        card = after if swap else before
        tt = t - B(4) if swap else t
        sc = 1 + (0.06 * (1 - ease(tt / 0.2)) if swap else 0)
        c = card.resize((int(cw * sc), int(ch * sc)), Image.BILINEAR)
        im.alpha_composite(c, ((W - c.width) // 2, 900 - (c.height - ch) // 2))
        d = ImageDraw.Draw(im); f = font(SANS_B, 46)
        lab = "AFTER  ロ長調 +2" if swap else "BEFORE  イ長調"
        col = GOLD if swap else WHITE
        d.text(((W - d.textlength(lab, font=f)) / 2, 820), lab, font=f, fill=col)
        kinetic(im, ["そのキー、", "2タップで変わる。"], t + 0.3, 330, size=120, hl=(1, RED))
        if swap: im = flash(im, tt, 0.1, 0.7)
        return im

    def cine(n, lines, tg, y=1150, hl=None, ss_frame=0):
        def r(t, i):
            im = punch(clips[n].at(i + ss_frame).convert("RGBA"), t)
            im = flash(im, t)
            if lines:
                g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
                gd.rectangle((0, y - 120, W, y + 420), fill=(0, 0, 0, 110)); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)))
                if tg: tag(im, tg, t, y - 60)
                kinetic(im, lines, t, y, size=104, hl=hl)
            return im
        return r

    def app(ph, lines, tg, bg_clip=None):
        def r(t, i):
            im = red_bg() if bg_clip is None else darken(slow_zoom(clips[bg_clip].at(i), t, 0.05).convert("RGBA"), 0.55)
            place_phone(im, ph, t, y0=700)
            tag(im, tg, t, 210)
            kinetic(im, lines, t, 270, size=100, hl=None)
            return flash(im, t, 0.1, 0.6)
        return r

    def endcard(t, i):
        im = darken(slow_zoom(clips[8].at(i), t, 0.03).convert("RGBA"), 0.62)
        d = ImageDraw.Draw(im)
        if icon:
            p = ease_back(t / 0.4); s = max(1, int(280 * p))
            ic = icon.resize((s, s), Image.BILINEAR); im.alpha_composite(ic, ((W - s) // 2, 560 + (280 - s) // 2))
        fw = font(SANS_B, 132); p = ease((t - 0.15) / 0.35)
        tr = int(60 - 36 * p); tw = text_w(d, "CRATE", fw, tr)
        draw_spaced(d, (W - tw) / 2, 900, "CRATE", fw, (255, 255, 255, int(255 * p)), tr)
        fs = font(SERIF, 54); s = "楽譜を、かんたん移調。"; p2 = ease((t - 0.35) / 0.35)
        d.text(((W - d.textlength(s, font=fs)) / 2, 1085 + (1 - p2) * 30), s, font=fs, fill=(240, 230, 215, int(255 * p2)))
        p3 = ease((t - 0.6) / 0.35)
        fp = font(SANS_B, 42); cta = "App Storeで「CRATE 移調」"
        cwid = d.textlength(cta, font=fp); bw = (cwid + 120) * p3; x0 = (W - bw) / 2
        if p3 > 0:
            d.rounded_rectangle((x0, 1230, x0 + bw, 1340), 55, fill=RED + (255,))
            if p3 > 0.6: d.text(((W - cwid) / 2, 1258), cta, font=fp, fill=WHITE)
        f2 = font(SANS_M, 34); s2 = "無料 ・ iPhone ・ iPad"
        d.text(((W - d.textlength(s2, font=f2)) / 2, 1385), s2, font=f2, fill=GOLD + (int(255 * p3),))
        return flash(im, t, 0.12, 0.8)

    timeline = [
        (7, hook),                                                               # 0   – 8 beats  (~3.9s) hook
        (2, cine(1, None, None)),                                                # quick energy
        (3, cine(4, ["印刷した楽譜を、", "撮るだけ。"], "SHOOT")),
        (3, app(ph_tp, ["♯ ♭ をタップ。"], "TRANSPOSE", bg_clip=None)),
        (2, cine(2, None, None)),
        (3, app(ph_done, ["音符も調号も、", "一瞬で書き換え。"], "ANY KEY")),
        (1, cine(7, None, None)),
        (3, cine(3, ["歌う人の", "キーで。"], "YOUR VOICE", hl=(1, RED))),
        (3, app(ph_pdf, ["PDFで、", "LINEへ。"], "SAVE · SHARE")),
        (1, cine(5, None, None)),
        (5, endcard),
    ]
    total = sum(b for b, _ in timeline) * beat
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", music, "-filter_complex",
                             f"[1:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={total-0.8:.3f}:d=0.8,loudnorm=I=-14:TP=-1.0:LRA=8[a]",
                             "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", out], stdin=subprocess.PIPE)
    t0 = 0.0; first = None
    for beats, fn in timeline:
        dur = beats * beat; n = int(round((t0 + dur) * FPS)) - int(round(t0 * FPS))
        for i in range(n):
            im = fn(i / FPS, i).convert("RGB")
            if first is None: first = im
            proc.stdin.write(im.tobytes())
        t0 += dur
    proc.stdin.close(); proc.wait()
    first.save(os.path.splitext(out)[0] + "_cover.jpg", quality=92)
    print("wrote", out, f"{total:.2f}s")


if __name__ == "__main__":
    main()
