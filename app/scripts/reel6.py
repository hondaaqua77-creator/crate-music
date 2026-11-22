#!/usr/bin/env python3
"""Reel 6: 'lower the key, then share it with a key card' (1.0.8 referral), reusing the reel 3 engine.
usage: reel6.py <clips_dir c1,c2.mp4 (r4)> <frames_dir (r6)> <music.mp3> <out.mp4> [bpm]"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reel3dyn import (W, H, FPS, SERIF, SANS_B, SANS_M, ROOT, RED, GOLD, WHITE, ease, ease_back, Clip, font, text_w,
                      draw_spaced, kinetic, tag, punch, slow_zoom, flash, darken, red_bg, rounded, phone_img, place_phone)


def band(im, y, h=560, a=120):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).rectangle((0, y - 140, W, y + h), fill=(0, 0, 0, a))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)))


def main():
    cd, fr, music, out = sys.argv[1:5]
    bpm = float(sys.argv[5]) if len(sys.argv) > 5 else 100.0
    beat = 60.0 / bpm
    clips = {1: Clip(os.path.join(cd, "c1.mp4"), ss=0.8), 2: Clip(os.path.join(cd, "c2.mp4"), ss=0.3), 4: Clip(os.path.join(cd, "c2.mp4"), ss=2.4)}
    ph = {k: phone_img(os.path.join(fr, f)) for k, f in (("score", "fr_b_score.png"), ("tp", "fr_score_tp.png"), ("refer", "fr_h_refer.png"))}
    card = Image.open(os.path.join(fr, "keycard.png")).convert("RGB")
    card = card.resize((740, 925), Image.LANCZOS)
    fr_ = Image.new("RGB", (740 + 36, 925 + 36), (255, 255, 255)); fr_.paste(card, (18, 18))
    card = rounded(fr_, 46)
    icon = os.path.join(ROOT, "icons", "icon-1024.png")
    icon = rounded(Image.open(icon).convert("RGB").resize((280, 280), Image.LANCZOS), 62) if os.path.exists(icon) else None

    def hook(t, i):
        im = slow_zoom(clips[1].at(i), t, 0.035).convert("RGBA"); band(im, 1120)
        tag(im, "合唱・弾き語りで", 1.0, 1060)
        kinetic(im, ["このキー、", "高すぎない…？"], t + 1.0, 1130, size=112, hl=(1, RED))
        return im

    def app(key, lines, tg, y0=700):
        def r(t, i):
            im = red_bg(); place_phone(im, ph[key], t, y0=y0)
            tag(im, tg, t, 210); kinetic(im, lines, t, 270, size=100)
            return flash(im, t, 0.1, 0.6)
        return r

    def cardshot(t, i):
        im = red_bg(); p = ease_back(t / 0.45); s = max(0.05, p)
        c = card.resize((max(1, int(card.width * s)), max(1, int(card.height * s))), Image.BILINEAR)
        rot = (1 - ease(t / 0.6)) * 12 - 3
        c = c.rotate(rot, resample=Image.BICUBIC, expand=True)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); x = (W - c.width) // 2; y = 720 + (950 - c.height) // 2
        if c.width > 120 and c.height > 120:
            ImageDraw.Draw(sh).rounded_rectangle((x + 30, y + 50, x + c.width - 30, y + c.height + 30), 60, fill=(0, 0, 0, 150))
            im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)))
        im.alpha_composite(c, (x, y))
        tag(im, "KEY CARD", t, 210); kinetic(im, ["QR付きで、", "そのまま紹介。"], t, 270, size=100)
        return flash(im, t, 0.1, 0.6)

    def happy(t, i):
        im = punch(clips[2].at(i).convert("RGBA"), t); im = flash(im, t, 0.12, 0.8); band(im, 1120)
        tag(im, "TOGETHER", t, 1060)
        kinetic(im, ["みんなで、", "歌いやすいキーへ。"], t, 1130, size=104, hl=(1, RED))
        return im

    def endcard(t, i):
        im = darken(slow_zoom(clips[4].at(i), t, 0.03).convert("RGBA"), 0.62); d = ImageDraw.Draw(im)
        if icon:
            p = ease_back(t / 0.4); s = max(1, int(280 * p))
            im.alpha_composite(icon.resize((s, s), Image.BILINEAR), ((W - s) // 2, 560 + (280 - s) // 2))
        fw = font(SANS_B, 132); p = ease((t - 0.15) / 0.35); tr = int(60 - 36 * p)
        draw_spaced(d, (W - text_w(d, "CRATE", fw, tr)) / 2, 900, "CRATE", fw, (255, 255, 255, int(255 * p)), tr)
        fs = font(SERIF, 54); s = "送ると、24時間 広告なし。"; p2 = ease((t - 0.35) / 0.35)
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
        (3, app("score", ["楽譜を撮って、"], "SHOOT")),
        (3, app("tp", ["♭♭ で", "2つ下げる。"], "TRANSPOSE")),
        (3, app("refer", ["仲間に、", "そのまま送れる。"], "SHARE", y0=760)),
        (4, cardshot),
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
