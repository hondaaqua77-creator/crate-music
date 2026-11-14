#!/usr/bin/env python3
"""Assemble the Higgsfield CM-style reel (editorial look): 4 clips -> serif captions -> end card -> mp4.
usage: reel-cm.py clip1.mp4 clip2.mp4 clip3.mp4 clip4.mp4 out.mp4
"""
import subprocess, sys, os, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-SemiBold.ttc"
SERIF_L = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc"
SANS_L = "/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc"
SANS_M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CLIP_LEN = 4.0
XF = 0.6          # crossfade length
END_LEN = 4.0
GOLD = (222, 196, 150)

# (serif headline lines, small english tag, y) – left aligned, editorial
CAPS = [
    (["写真を撮るだけで、", "楽譜を移調。"], "SHOOT  ·  TRANSPOSE", 520),
    (["♯ ♭ をタップ。", "音符も調号も、", "書き換わる。"], "ANY KEY, IN SECONDS", 480),
    (["歌う人のキーで、", "そのまま弾ける。"], "PLAY IN THEIR KEY", 520),
    (["PDFで保存して、LINEへ。"], "SAVE  ·  SHARE", 110),
]


def spaced(d, xy, txt, font, fill, tracking):
    x, y = xy
    for ch in txt:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking


def spaced_len(d, txt, font, tracking):
    return sum(d.textlength(ch, font=font) for ch in txt) + tracking * (len(txt) - 1)


def caption_png(path, lines, tag, y, size=84):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fh = ImageFont.truetype(SERIF_B, size)
    ft = ImageFont.truetype(SANS_M, 30)
    x0 = 96
    # shadow layer for legibility
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    # gold accent rule + tag
    sd.rectangle((x0, y - 44, x0 + 54, y - 41), fill=(0, 0, 0, 160))
    d.rectangle((x0, y - 44, x0 + 54, y - 41), fill=GOLD + (255,))
    spaced(sd, (x0 + 72, y - 62), tag, ft, (0, 0, 0, 160), 6)
    spaced(d, (x0 + 72, y - 62), tag, ft, GOLD + (255,), 6)
    yy = y
    for ln in lines:
        spaced(sd, (x0, yy), ln, fh, (0, 0, 0, 180), 2)
        spaced(d, (x0, yy), ln, fh, (255, 255, 255, 255), 2)
        yy += int(size * 1.32)
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    Image.alpha_composite(sh, im).save(path)


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    im = im.convert("RGBA")
    im.putalpha(m)
    return im


def end_card(path):
    # deep navy -> warm black gradient with a soft gold glow
    im = Image.new("RGB", (W, H), (10, 11, 16))
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((140, 420, W - 140, 1200), fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(260))
    im = Image.composite(Image.new("RGB", (W, H), (96, 70, 38)), im, glow)
    d = ImageDraw.Draw(im)
    # app icon
    icon_p = os.path.join(ROOT, "..", "icons", "icon-1024.png")
    if os.path.exists(icon_p):
        ic = rounded(Image.open(icon_p).convert("RGB").resize((260, 260), Image.LANCZOS), 58)
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle(((W - 260) // 2, 570, (W + 260) // 2, 830), 58, fill=(0, 0, 0, 140))
        shadow = shadow.filter(ImageFilter.GaussianBlur(30))
        im = Image.alpha_composite(im.convert("RGBA"), shadow)
        im.paste(ic, ((W - 260) // 2, 540), ic)
        im = im.convert("RGB")
        d = ImageDraw.Draw(im)
    # wordmark
    fw = ImageFont.truetype(SANS_M, 118)
    tw = spaced_len(d, "CRATE", fw, 22)
    spaced(d, ((W - tw) / 2, 860), "CRATE", fw, (255, 255, 255), 22)
    fs = ImageFont.truetype(SERIF_L, 50)
    t = "楽譜を、かんたん移調。"
    d.text(((W - d.textlength(t, font=fs)) / 2, 1020), t, font=fs, fill=(235, 228, 215))
    # thin rule
    d.rectangle((W // 2 - 40, 1120, W // 2 + 40, 1121), fill=GOLD)
    ft = ImageFont.truetype(SANS_M, 30)
    t2 = "FREE  ·  iPhone  ·  iPad"
    tw2 = spaced_len(d, t2, ft, 5)
    spaced(d, ((W - tw2) / 2, 1160), t2, ft, GOLD, 5)
    # pill CTA
    fp = ImageFont.truetype(SANS_M, 40)
    cta = "App Store で「CRATE 移調」と検索"
    cw = d.textlength(cta, font=fp)
    px, py, ph = (W - cw) / 2 - 56, 1270, 108
    d.rounded_rectangle((px, py, px + cw + 112, py + ph), 54, outline=(255, 255, 255), width=2)
    d.text(((W - cw) / 2, py + 30), cta, font=fp, fill=(255, 255, 255))
    im.save(path)


def main():
    clips, out = sys.argv[1:5], sys.argv[5]
    tmp = tempfile.mkdtemp()
    parts = []
    grade = "eq=contrast=1.06:saturation=0.92:brightness=-0.02,vignette=PI/4.2,unsharp=3:3:0.4"
    for i, (c, (lines, tag, y)) in enumerate(zip(clips, CAPS)):
        ov = os.path.join(tmp, f"cap{i}.png")
        caption_png(ov, lines, tag, y, size=84 if i < 3 else 66)
        p = os.path.join(tmp, f"part{i}.mp4")
        vf = (
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"trim=0:{CLIP_LEN},setpts=PTS-STARTPTS,{grade}[v];"
            f"[1:v]format=rgba,fade=t=in:st=0.5:d=0.5:alpha=1,fade=t=out:st={CLIP_LEN-0.7}:d=0.5:alpha=1[o];"
            f"[v][o]overlay=0:0:shortest=1,format=yuv420p"
        )
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", c, "-loop", "1", "-t", str(CLIP_LEN), "-i", ov,
                        "-filter_complex", vf, "-an", "-r", "30", "-c:v", "libx264", "-crf", "16", "-preset", "medium", p], check=True)
        parts.append(p)
    ec = os.path.join(tmp, "end.png")
    end_card(ec)
    pe = os.path.join(tmp, "end.mp4")
    # slow push-in on the end card for life
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", str(END_LEN), "-i", ec,
                    "-vf", f"scale=1296:2304,zoompan=z='1.0+0.0004*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30,format=yuv420p",
                    "-r", "30", "-c:v", "libx264", "-crf", "16", pe], check=True)
    parts.append(pe)
    # crossfade chain
    n = len(parts)
    inputs = []
    for p in parts:
        inputs += ["-i", p]
    durs = [CLIP_LEN] * 4 + [END_LEN]
    fc, prev, off = "", "[0:v]", 0.0
    for k in range(1, n):
        off += durs[k - 1] - XF
        trans = "fade" if k < n - 1 else "fadeblack"
        lbl = f"[x{k}]" if k < n - 1 else "[vout]"
        fc += f"{prev}[{k}:v]xfade=transition={trans}:duration={XF}:offset={off:.2f}{lbl};"
        prev = lbl
    fc = fc.rstrip(";") + ",fade=t=in:st=0:d=0.4,fade=t=out:st=%.2f:d=0.6[vfin]" % (off + END_LEN - 0.6)
    fc = fc.replace("[vout];", "[vout];[vout]")  # no-op guard
    fc = fc.replace("[vout],fade", "[vout];[vout]fade")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs,
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-filter_complex", fc, "-map", "[vfin]", "-map", f"{n}:a", "-shortest",
                    "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart", out], check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
