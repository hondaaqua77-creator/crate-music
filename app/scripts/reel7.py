#!/usr/bin/env python3
"""Reel 7: wind band — rewriting a concert-pitch part for a transposing instrument, reusing the reel 3 engine.
usage: reel7.py <clips_dir c1,c2.mp4> <frames_dir fr_*.png> <music.mp3> <out.mp4> [bpm]
c1 = sax player puzzled at the score, c2 = band playing happily
"""
import os, subprocess, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reel3dyn import (W, H, FPS, SERIF, SANS_B, SANS_M, ROOT, RED, GOLD, WHITE, ease, ease_back, Clip, font, text_w,
                      draw_spaced, kinetic, tag, punch, slow_zoom, flash, darken, red_bg, rounded, phone_img, place_phone)


def band(im, y, h=560, a=120):
    from PIL import ImageFilter
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).rectangle((0, y - 140, W, y + h), fill=(0, 0, 0, a))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)))


def main():
    cd, fr, music, out = sys.argv[1:5]
    bpm = float(sys.argv[5]) if len(sys.argv) > 5 else 100.0
    beat = 60.0 / bpm
    clips = {1: Clip(os.path.join(cd, "c1.mp4"), ss=0.3), 2: Clip(os.path.join(cd, "c2.mp4"), ss=0.3),
             4: Clip(os.path.join(cd, "c2.mp4"), ss=2.4)}
    ph = {k: phone_img(os.path.join(fr, f)) for k, f in (("score", "fr_b_score.png"), ("tp", "fr_c_tp.png"), ("pdf", "fr_g_pdf.png"))}
    icon = os.path.join(ROOT, "icons", "icon-1024.png")
    icon = rounded(Image.open(icon).convert("RGB").resize((280, 280), Image.LANCZOS), 62) if os.path.exists(icon) else None

    def hook(t, i):  # text visible from frame 0
        im = slow_zoom(clips[1].at(i), t, 0.035).convert("RGBA")
        band(im, 1120)
        tag(im, "吹奏楽あるある", 1.0, 1060)
        kinetic(im, ["ピアノ譜を", "サックス用に", "直すのがツラい…"], t + 1.0, 1080, size=100, hl=(2, RED))
        return im

    def app(key, lines, tg):
        def r(t, i):
            im = red_bg(); place_phone(im, ph[key], t, y0=700)
            tag(im, tg, t, 210); kinetic(im, lines, t, 270, size=100)
            return flash(im, t, 0.1, 0.6)
        return r

    def happy(t, i):
        im = punch(clips[2].at(i).convert("RGBA"), t); im = flash(im, t, 0.12, 0.8)
        band(im, 1120)
        tag(im, "WIND BAND", t, 1060)
        kinetic(im, ["練習時間は、", "音楽のために。"], t, 1130, size=104, hl=(1, RED))
        return im

    def endcard(t, i):
        im = darken(slow_zoom(clips[4].at(i), t, 0.03).convert("RGBA"), 0.62)
        d = ImageDraw.Draw(im)
        if icon:
            p = ease_back(t / 0.4); s = max(1, int(280 * p))
            im.alpha_composite(icon.resize((s, s), Image.BILINEAR), ((W - s) // 2, 560 + (280 - s) // 2))
        fw = font(SANS_B, 132); p = ease((t - 0.15) / 0.35); tr = int(60 - 36 * p)
        draw_spaced(d, (W - text_w(d, "CRATE", fw, tr)) / 2, 900, "CRATE", fw, (255, 255, 255, int(255 * p)), tr)
        fs = font(SERIF, 54); s = "楽譜を、かんたん移調。"; p2 = ease((t - 0.35) / 0.35)
        d.text(((W - d.textlength(s, font=fs)) / 2, 1085 + (1 - p2) * 30), s, font=fs, fill=(240, 230, 215, int(255 * p2)))
        p3 = ease((t - 0.6) / 0.35); fp = font(SANS_B, 42); cta = "App Storeで「CRATE 移調」"
        cw = d.textlength(cta, font=fp); bw = (cw + 120) * p3; x0 = (W - bw) / 2
        if p3 > 0:
            d.rounded_rectangle((x0, 1230, x0 + bw, 1340), 55, fill=RED + (255,))
            if p3 > 0.6: d.text(((W - cw) / 2, 1258), cta, font=fp, fill=WHITE)
        f2 = font(SANS_M, 34); s2 = "無料 ・ iPhone ・ iPad"
        d.text(((W - d.textlength(s2, font=f2)) / 2, 1385), s2, font=f2, fill=GOLD + (int(255 * p3),))
        return flash(im, t, 0.12, 0.8)

    timeline = [
        (5, hook),
        (3, app("score", ["CRATEなら、", "楽譜を撮るだけ。"], "SHOOT")),
        (3, app("tp", ["半音ずつ、", "♯ ♭ で移調。"], "B♭ / E♭ / F")),
        (3, app("pdf", ["パートのみんなに、", "PDFで配れる。"], "SHARE")),
        (4, happy),
        (5, endcard),
    ]
    total = sum(b for b, _ in timeline) * beat
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", music, "-filter_complex",
                             f"[1:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={total-0.8:.3f}:d=0.8,loudnorm=I=-14:TP=-1.0:LRA=8[a]",
                             "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "21", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", out], stdin=subprocess.PIPE)
    t0 = 0.0; first = None
    for beats, fn in timeline:
        n = int(round((t0 + beats * beat) * FPS)) - int(round(t0 * FPS))
        for i in range(n):
            im = fn(i / FPS, i).convert("RGB")
            if first is None: first = im
            proc.stdin.write(im.tobytes())
        t0 += beats * beat
    proc.stdin.close(); proc.wait()
    first.save(os.path.splitext(out)[0] + "_cover.jpg", quality=92)
    print("wrote", out, f"{total:.2f}s")


if __name__ == "__main__":
    main()
