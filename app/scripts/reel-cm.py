#!/usr/bin/env python3
"""Assemble the Higgsfield CM-style reel: 4 clips -> captions (PNG overlays) -> end card -> mp4.
usage: reel-cm.py clip1.mp4 clip2.mp4 clip3.mp4 clip4.mp4 out.mp4
"""
import subprocess, sys, os, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
CLIP_LEN = 4.0  # seconds used from each 5s clip
END_LEN = 3.5

# (big line, small line) per clip – kept in the upper-middle safe zone
CAPS = [
    ("写真を撮るだけで、", "楽譜を移調。"),
    ("♯♭をタップ。", "音符も調号も、書き換わる。"),
    ("歌う人のキーで、", "そのまま弾ける。"),
    ("PDFで保存して、LINEへ。", ""),
]
CAP_Y = [520, 520, 520, 120]  # clip 4: above the phone


def text_png(path, big, small, big_size=96, small_size=58, y=560):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fb = ImageFont.truetype(FONT_BLACK, big_size)
    fs = ImageFont.truetype(FONT, small_size)
    # soft shadow layer
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    for txt, f, yy in ((big, fb, y), (small, fs, y + big_size + 36)):
        w = d.textlength(txt, font=f)
        x = (W - w) / 2
        sd.text((x, yy), txt, font=f, fill=(0, 0, 0, 170))
        d.text((x, yy), txt, font=f, fill=(255, 255, 255, 255))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    out = Image.alpha_composite(sh, im)
    out.save(path)


def end_card(path):
    im = Image.new("RGB", (W, H), (14, 14, 18))
    d = ImageDraw.Draw(im)
    # subtle warm vignette
    g = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(g)
    gd.ellipse((-200, 300, W + 200, H - 300), fill=90)
    g = g.filter(ImageFilter.GaussianBlur(220))
    warm = Image.new("RGB", (W, H), (120, 80, 40))
    im = Image.composite(warm, im, g)
    d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(FONT_BLACK, 150)
    f2 = ImageFont.truetype(FONT, 60)
    f3 = ImageFont.truetype(FONT, 46)
    lines = [
        ("CRATE", f1, 600, (255, 255, 255)),
        ("楽譜をかんたん移調", f2, 790, (255, 255, 255)),
        ("無料  ·  iPhone / iPad", f3, 920, (220, 200, 170)),
        ("App Storeで「CRATE 移調」と検索", f3, 1040, (255, 255, 255)),
    ]
    for txt, f, y, col in lines:
        w = d.textlength(txt, font=f)
        d.text(((W - w) / 2, y), txt, font=f, fill=col)
    # QR if available
    qr = os.path.join(os.path.dirname(__file__), "..", "store", "reach", "qr.png")
    if os.path.exists(qr):
        q = Image.open(qr).convert("RGB").resize((300, 300))
        im.paste(q, ((W - 300) // 2, 1180))
    im.save(path)


def main():
    clips, out = sys.argv[1:5], sys.argv[5]
    tmp = tempfile.mkdtemp()
    parts = []
    for i, (c, (big, small)) in enumerate(zip(clips, CAPS)):
        ov = os.path.join(tmp, f"cap{i}.png")
        text_png(ov, big, small, y=CAP_Y[i], big_size=96 if i < 3 else 74, small_size=58 if i < 3 else 52)
        p = os.path.join(tmp, f"part{i}.mp4")
        # scale/crop to 1080x1920, trim, fade in/out, overlay caption with fade
        vf = (
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"trim=0:{CLIP_LEN},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.35,fade=t=out:st={CLIP_LEN-0.4}:d=0.4[v];"
            f"[1:v]format=rgba,fade=t=in:st=0.45:d=0.4:alpha=1,fade=t=out:st={CLIP_LEN-0.6}:d=0.4:alpha=1[o];"
            f"[v][o]overlay=0:0:shortest=1,format=yuv420p"
        )
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", c, "-loop", "1", "-t", str(CLIP_LEN), "-i", ov,
                        "-filter_complex", vf, "-an", "-r", "30", "-c:v", "libx264", "-crf", "18", "-preset", "medium", p], check=True)
        parts.append(p)
    ec = os.path.join(tmp, "end.png")
    end_card(ec)
    pe = os.path.join(tmp, "end.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", str(END_LEN), "-i", ec,
                    "-vf", f"fade=t=in:st=0:d=0.5,fade=t=out:st={END_LEN-0.5}:d=0.5,format=yuv420p",
                    "-r", "30", "-c:v", "libx264", "-crf", "18", pe], check=True)
    parts.append(pe)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    # silent audio track so Instagram accepts it; user adds music in-app
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart", out], check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
