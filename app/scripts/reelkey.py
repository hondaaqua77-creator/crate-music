#!/usr/bin/env python3
"""Creative CM reel "Find your key." — key/lock metaphor, cinematic finish.
Letterbox, film grain, light leaks, editorial serif type (per-letter fade), dissolves, real app screens in a floating phone.
usage: reelkey.py <clips_dir k1..k4.mp4> <frames_dir fr_*.png> <music.mp3> <out.mp4> [bpm]
k1 key descends, k2 key turns / notes shift, k3 singer in spotlight, k4 hands on keys
"""
import math, os, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reel3dyn import Clip, rounded, ease

W, H, FPS = 1080, 1920, 30
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-SemiBold.ttc"
SERIF_L = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc"
SANS_M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
GOLD, CREAM, RED = (226, 196, 140), (244, 236, 222), (196, 44, 64)
BAR = 96          # letterbox bar height
XF = 0.28         # dissolve
CROP = (40, 280, 760, 560)
F = {}


def font(p, s):
    k = (p, s)
    if k not in F: F[k] = ImageFont.truetype(p, s)
    return F[k]


def tw(d, s, f, tr):
    return sum(d.textlength(c, font=f) for c in s) + tr * (len(s) - 1)


def type_line(im, s, t, y, size, path=SERIF_B, color=CREAM, tr=6, per=0.045, center=True, x0=110):
    """editorial reveal: each glyph fades + rises a few px, slightly staggered"""
    d = ImageDraw.Draw(im); f = font(path, size)
    x = (W - tw(d, s, f, tr)) / 2 if center else x0
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for i, c in enumerate(s):
        p = ease((t - i * per) / 0.45)
        if p > 0:
            yy = y + (1 - p) * 14
            ld.text((x, yy), c, font=f, fill=color + (int(255 * p),))
            sd.text((x, yy + 4), c, font=f, fill=(0, 0, 0, int(150 * p)))
        x += d.textlength(c, font=f) + tr
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10))); im.alpha_composite(lay)


def tag(im, s, t, y, color=GOLD, center=True, x0=110):
    d = ImageDraw.Draw(im); f = font(SANS_M, 28); p = ease(t / 0.5); tr = 10
    w = tw(d, s, f, tr); x = (W - w) / 2 if center else x0
    lw = 46 * p
    if center:
        d.line((W / 2 - w / 2 - 70, y + 18, W / 2 - w / 2 - 70 + lw, y + 18), fill=color + (int(255 * p),), width=2)
        d.line((W / 2 + w / 2 + 70 - lw, y + 18, W / 2 + w / 2 + 70, y + 18), fill=color + (int(255 * p),), width=2)
    for c in s:
        d.text((x, y), c, font=f, fill=color + (int(255 * p),)); x += d.textlength(c, font=f) + tr


def kenburns(img, t, z0=1.0, z1=1.06, dx=0, dy=0, dur=3.0):
    k = min(1, t / dur); z = z0 + (z1 - z0) * k
    w, h = int(W * z), int(H * z)
    im = img.resize((w, h), Image.BILINEAR)
    ox = (w - W) // 2 + int(dx * k); oy = (h - H) // 2 + int(dy * k)
    return im.crop((ox, oy, ox + W, oy + H))


def grade(img, warm=1.0):
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255
    a = a ** 1.06                                   # deeper shadows
    a[..., 0] *= 1.0 + 0.04 * warm; a[..., 2] *= 1.0 - 0.05 * warm
    lum = a.mean(axis=2, keepdims=True)
    a = lum + (a - lum) * 0.9                        # slightly desaturated, filmic
    a *= VIGM
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


_yy, _xx = np.mgrid[0:H, 0:W]
VIGM = np.clip(1.15 - 0.45 * np.sqrt(((_xx - W / 2) / (W * .62)) ** 2 + ((_yy - H / 2) / (H * .62)) ** 2), 0.45, 1)[..., None].astype(np.float32)
GRAIN = [np.random.default_rng(i).normal(0, 9, (H // 2, W // 2)).astype(np.float32) for i in range(6)]


def finish(img, gi, leak=0.0):
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    g = GRAIN[gi % len(GRAIN)]; g = np.kron(g, np.ones((2, 2), np.float32))[:H, :W]
    a += g[..., None]
    if leak > 0:  # warm red/gold light leak from the right edge
        xx = np.linspace(0, 1, W)[None, :, None]
        m = np.clip((xx - 0.55) / 0.45, 0, 1) ** 2 * leak
        a = a * (1 - m * 0.35) + np.array([255, 120, 70], np.float32) * m * 0.55
    a[:BAR] = 0; a[H - BAR:] = 0
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def phone(src, width=620):
    sc = Image.open(src).convert("RGB"); h = int(sc.height * width / sc.width)
    sc = sc.resize((width, h), Image.LANCZOS); b = 14
    body = Image.new("RGBA", (width + 2 * b, h + 2 * b), (0, 0, 0, 0))
    ImageDraw.Draw(body).rounded_rectangle((0, 0, body.width - 1, body.height - 1), 80, fill=(16, 16, 18, 255), outline=(150, 128, 92, 255), width=3)
    s = rounded(sc, 68); body.paste(s, (b, b), s)
    return body


def main():
    cd, fr, music, out = sys.argv[1:5]
    bpm = float(sys.argv[5]) if len(sys.argv) > 5 else 90.0
    beat = 60.0 / bpm
    K = {n: Clip(os.path.join(cd, f"k{n}.mp4"), ss=s) for n, s in ((1, 0.2), (2, 1.6), (3, 1.6), (4, 1.4))}
    ph_before, ph_after = phone(os.path.join(fr, "fr_b_score.png")), phone(os.path.join(fr, "fr_f_done.png"))
    icon = os.path.join(ROOT, "icons", "icon-1024.png")
    icon = rounded(Image.open(icon).convert("RGB").resize((230, 230), Image.LANCZOS), 52) if os.path.exists(icon) else None

    def s_key(t):  # hook: text present at frame 0
        im = grade(kenburns(K[1].at(int(t * FPS)), t, 1.0, 1.07, dur=4 * beat)).convert("RGBA")
        tag(im, "CRATE", 1.0, BAR + 90)
        type_line(im, "原曲のキーが、", t + 1.0, 1210, 92)
        type_line(im, "高すぎる。", t + 1.0, 1340, 92, per=0.06)
        return im, 0.0

    def s_turn(t):
        im = grade(kenburns(K[2].at(int(t * FPS)), t, 1.04, 1.12, dur=3 * beat)).convert("RGBA")
        type_line(im, "その楽譜に、", t, 1210, 88)
        type_line(im, "合う鍵を。", t - 0.35, 1335, 104, color=GOLD, per=0.07)
        return im, 0.35 + 0.25 * math.sin(t * 2)

    def s_app(t):
        bg = Image.new("RGB", (W, H), (14, 10, 12))
        gl = Image.new("L", (W, H), 0); ImageDraw.Draw(gl).ellipse((60, 520, W - 60, 1560), fill=150)
        bg = Image.composite(Image.new("RGB", (W, H), (110, 26, 40)), bg, gl.filter(ImageFilter.GaussianBlur(240))).convert("RGBA")
        swap = ease((t - 1.0) / 0.5)
        p = Image.blend(ph_before.convert("RGBA"), ph_after.convert("RGBA"), swap)
        z = 1.0 + 0.03 * t; pw, phh = int(p.width * z), int(p.height * z); p = p.resize((pw, phh), Image.BILINEAR)
        y = int(470 - 18 * t)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); x = (W - pw) // 2
        ImageDraw.Draw(sh).rounded_rectangle((x + 20, y + 60, x + pw - 20, y + phh + 40), 90, fill=(0, 0, 0, 200))
        bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(50))); bg.alpha_composite(p, (x, y))
        cut = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(cut).rectangle((0, 1180, W, H), fill=(14, 10, 12, 255))
        g2 = Image.new("L", (W, H), 0); ImageDraw.Draw(g2).rectangle((0, 1180, W, H), fill=255)
        bg = Image.composite(Image.alpha_composite(bg, cut), bg, g2.filter(ImageFilter.GaussianBlur(70)))
        tag(bg, "TRANSPOSE", t, BAR + 80)
        type_line(bg, "♯ ♭ をタップするだけ。", t, 1290, 74)
        type_line(bg, "音符も調号も、書き換わる。", t - 0.5, 1400, 52, path=SERIF_L, tr=4)
        return bg, 0.0

    def s_sing(t):
        im = grade(kenburns(K[3].at(int(t * FPS)), t, 1.02, 1.1, dur=4 * beat)).convert("RGBA")
        type_line(im, "あなたのキーで、", t, 1250, 90)
        type_line(im, "歌おう。", t - 0.4, 1375, 112, color=GOLD, per=0.08)
        return im, 0.2

    def s_keys(t):
        im = grade(kenburns(K[4].at(int(t * FPS)), t, 1.0, 1.08, dx=-30, dur=3 * beat)).convert("RGBA")
        type_line(im, "写真1枚で、楽譜を移調。", t, 1330, 66, path=SERIF_L, tr=5)
        return im, 0.45

    def s_end(t):
        im = Image.new("RGB", (W, H), (10, 9, 11))
        gl = Image.new("L", (W, H), 0); ImageDraw.Draw(gl).ellipse((120, 460, W - 120, 1260), fill=120)
        im = Image.composite(Image.new("RGB", (W, H), (98, 58, 30)), im, gl.filter(ImageFilter.GaussianBlur(260))).convert("RGBA")
        if icon:
            p = ease(t / 0.6); s = int(230 * (0.92 + 0.08 * p))
            ic = icon.resize((s, s), Image.BILINEAR); a = ic.split()[3].point(lambda v: int(v * p)); ic.putalpha(a)
            im.alpha_composite(ic, ((W - s) // 2, 560 + (230 - s) // 2))
        d = ImageDraw.Draw(im); fw = font(SANS_M, 112); p = ease((t - 0.3) / 0.6); tr = int(44 - 20 * p); s = "CRATE"
        x = (W - tw(d, s, fw, tr)) / 2
        for c in s:
            d.text((x, 860), c, font=fw, fill=(255, 255, 255, int(255 * p))); x += d.textlength(c, font=fw) + tr
        type_line(im, "Find your key.", t - 0.7, 1015, 56, path=SERIF_L, color=GOLD, tr=3, per=0.03)
        p3 = ease((t - 1.3) / 0.5)
        d.line((W / 2 - 40 * p3, 1110, W / 2 + 40 * p3, 1110), fill=GOLD + (255,), width=2)
        fp = font(SANS_M, 38); cta = "App Store で「CRATE 移調」"; cw = d.textlength(cta, font=fp)
        px = (W - cw) / 2 - 54
        d.rounded_rectangle((px, 1160, px + cw + 108, 1262), 51, outline=(255, 255, 255, int(255 * p3)), width=2)
        d.text(((W - cw) / 2, 1186), cta, font=fp, fill=(255, 255, 255, int(255 * p3)))
        f2 = font(SANS_M, 28); s2 = "FREE  ·  iPhone  ·  iPad"; x = (W - tw(d, s2, f2, 6)) / 2
        for c in s2:
            d.text((x, 1300), c, font=f2, fill=GOLD + (int(255 * p3),)); x += d.textlength(c, font=f2) + 6
        return im, 0.0

    scenes = [(4, s_key), (3, s_turn), (3, s_app), (4, s_sing), (3, s_keys), (6, s_end)]
    starts, t0 = [], 0.0
    for b, fn in scenes:
        starts.append((t0, b * beat, fn)); t0 += b * beat
    total = t0
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", music, "-filter_complex",
                             f"[1:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={total-1.2:.3f}:d=1.2,loudnorm=I=-14:TP=-1.0:LRA=8[a]",
                             "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", out], stdin=subprocess.PIPE)
    first = None
    for n in range(int(round(total * FPS))):
        T = n / FPS
        k = max(i for i, (s, _, _) in enumerate(starts) if s <= T + 1e-9)
        s0, dur, fn = starts[k]
        im, leak = fn(T - s0)
        if k + 1 < len(starts) and T > s0 + dur - XF:  # dissolve into next shot
            ns, _, nfn = starts[k + 1]; nim, nleak = nfn(max(0, T - ns))
            a = (T - (s0 + dur - XF)) / XF
            im = Image.blend(im.convert("RGB"), nim.convert("RGB"), a); leak = leak * (1 - a) + nleak * a
        if fn is s_end and T - s0 > dur - 0.6:  # fade out
            im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H)), (T - (s0 + dur - 0.6)) / 0.6)
        fr_img = finish(im, n // 2, leak)
        if first is None: first = fr_img
        proc.stdin.write(fr_img.tobytes())
    proc.stdin.close(); proc.wait()
    first.save(os.path.splitext(out)[0] + "_cover.jpg", quality=93)
    print("wrote", out, f"{total:.2f}s")


if __name__ == "__main__":
    main()
