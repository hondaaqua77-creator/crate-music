#!/usr/bin/env python3
"""Reel 4: problem -> solution ("原キーだと高くて歌えない"), beat-synced, reusing the reel 3 engine.
usage: reel4.py <clips_dir c1..c3.mp4> <frames_dir fr_*.png> <music.mp3> <out.mp4> [bpm]
c1 = singer's voice cracks, c2 = singing happily, c3 = rewriting a score by hand
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
    clips = {1: Clip(os.path.join(cd, "c1.mp4"), ss=0.8), 2: Clip(os.path.join(cd, "c2.mp4"), ss=0.3),
             3: Clip(os.path.join(cd, "c3.mp4"), ss=1.0), 4: Clip(os.path.join(cd, "c2.mp4"), ss=2.4)}
    ph = {k: phone_img(os.path.join(fr, f)) for k, f in (("score", "fr_b_score.png"), ("tp", "fr_c_tp.png"), ("done", "fr_f_done.png"))}
    icon = os.path.join(ROOT, "icons", "icon-1024.png")
    icon = rounded(Image.open(icon).convert("RGB").resize((280, 280), Image.LANCZOS), 62) if os.path.exists(icon) else None

    def hook(t, i):  # text visible from frame 0
        im = slow_zoom(clips[1].at(i), t, 0.035).convert("RGBA")
        band(im, 1120)
        tag(im, "弾き語りあるある", 1.0, 1060)
        kinetic(im, ["原曲キーだと、", "高くて歌えない…"], t + 1.0, 1130, size=112, hl=(1, RED))
        return im

    def pain(t, i):
        im = punch(clips[3].at(i).convert("RGBA"), t); im = flash(im, t, 0.1, 0.6)
        band(im, 1120)
        kinetic(im, ["手で書き直す？"], t, 1130, size=112)
        d = ImageDraw.Draw(im); f = font(SANS_B, 112); tw = text_w(d, "手で書き直す？", f, 2)
        p = ease((t - 0.45) / 0.25)
        if p > 0:
            x0 = (W - tw) / 2 - 20
            d.line((x0, 1200, x0 + (tw + 40) * p, 1200), fill=RED + (255,), width=14)
        if t > 0.75:
            k = ease((t - 0.75) / 0.25); fs = font(SANS_B, 64); s = "時間がかかりすぎる。"
            d.text(((W - d.textlength(s, font=fs)) / 2, 1300 + (1 - k) * 30), s, font=fs, fill=GOLD + (int(255 * k),))
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
        tag(im, "YOUR KEY", t, 1060)
        kinetic(im, ["自分のキーで、", "気持ちよく歌える。"], t, 1130, size=104, hl=(1, RED))
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
        (3, pain),
        (3, app("score", ["CRATEなら、", "楽譜を撮るだけ。"], "SHOOT")),
        (3, app("tp", ["♯ ♭ をタップ。"], "TRANSPOSE")),
        (3, app("done", ["音符も調号も、", "一瞬で書き換え。"], "ANY KEY")),
        (4, happy),
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
