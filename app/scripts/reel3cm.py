#!/usr/bin/env python3
"""Reel 3 (CM edition): editorial/luxury look + real app screens + before/after hook at frame 0.
usage: reel3cm.py <frames_dir> <reach_dir> <music.mp3> <out.mp4>
frames_dir: fr_*.png from reel-shoot.py ; reach_dir: app/store/reach (cm/, r2/ clips)
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-SemiBold.ttc"
SERIF_L = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc"
SANS_M = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
GOLD = (222, 196, 150)
CROP = (40, 280, 760, 560)
XF = 0.45
GRADE = "eq=contrast=1.06:saturation=0.92:brightness=-0.02,vignette=PI/4.2"


def spaced(d, xy, txt, font, fill, tr):
    x, y = xy
    for ch in txt:
        d.text((x, y), ch, font=font, fill=fill); x += d.textlength(ch, font=font) + tr


def slen(d, txt, font, tr):
    return sum(d.textlength(c, font=font) for c in txt) + tr * (len(txt) - 1)


def dark_bg():
    im = Image.new("RGB", (W, H), (12, 11, 14))
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse((80, 520, W - 80, 1500), fill=110)
    g = g.filter(ImageFilter.GaussianBlur(280))
    im = Image.composite(Image.new("RGB", (W, H), (110, 34, 46)), im, g)  # brand-red glow
    return im


def caption_layer(lines, tag, y, size=80, center=False):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    fh = ImageFont.truetype(SERIF_B, size); ft = ImageFont.truetype(SANS_M, 30)
    x0 = 96
    if tag:
        tx = (W - slen(d, tag, ft, 6)) / 2 if center else x0 + 72
        if not center:
            for dd, c in ((sd, (0, 0, 0, 170)), (d, GOLD + (255,))):
                dd.rectangle((x0, y - 44, x0 + 54, y - 41), fill=c)
        for dd, c in ((sd, (0, 0, 0, 170)), (d, GOLD + (255,))):
            spaced(dd, (tx, y - 62), tag, ft, c, 6)
    yy = y
    for ln in lines:
        lx = (W - slen(d, ln, fh, 2)) / 2 if center else x0
        spaced(sd, (lx, yy), ln, fh, (0, 0, 0, 200), 2)
        spaced(d, (lx, yy), ln, fh, (255, 255, 255, 255), 2)
        yy += int(size * 1.32)
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    return Image.alpha_composite(sh, im)


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    o = im.convert("RGBA"); o.putalpha(m); return o


def shadowed(base, im, x, y, r, blur=30, alpha=150):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x, y + 18, x + im.width, y + im.height + 18), r, fill=(0, 0, 0, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base = Image.alpha_composite(base.convert("RGBA"), sh)
    ri = rounded(im, r); base.paste(ri, (x, y), ri)
    return base


def phone(src, width=640):
    """real app screen inside a thin graphite bezel"""
    sc = Image.open(src).convert("RGB")
    h = int(sc.height * width / sc.width)
    sc = sc.resize((width, h), Image.LANCZOS)
    b = 16
    body = Image.new("RGBA", (width + 2 * b, h + 2 * b), (0, 0, 0, 0))
    ImageDraw.Draw(body).rounded_rectangle((0, 0, body.width - 1, body.height - 1), 86, fill=(28, 28, 32, 255),
                                           outline=(120, 108, 92, 255), width=3)
    s = rounded(sc, 72); body.paste(s, (b, b), s)
    return body


def phone_still(src, lines, tag, cap_y=150):
    im = dark_bg().convert("RGBA")
    ph = phone(src)
    x, y = (W - ph.width) // 2, 560
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x + 10, y + 40, x + ph.width - 10, y + ph.height + 30), 90, fill=(0, 0, 0, 190))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(40)))
    im.paste(ph, (x, y), ph)
    return Image.alpha_composite(im, caption_layer(lines, tag, cap_y, size=74)).convert("RGB")


def hook_still(fr):
    im = dark_bg().convert("RGBA")
    im = Image.alpha_composite(im, caption_layer(["そのキー、", "2タップで変える。"], "TRANSPOSE  ·  IN SECONDS", 260, size=96, center=True))
    a = Image.open(os.path.join(fr, "fr_b_score.png")).convert("RGB").crop(CROP)
    b = Image.open(os.path.join(fr, "fr_f_done.png")).convert("RGB").crop(CROP)
    cw = 900; ch = int(a.height * cw / a.width)
    a = a.resize((cw, ch), Image.LANCZOS); b = b.resize((cw, ch), Image.LANCZOS)
    x = (W - cw) // 2
    d = ImageDraw.Draw(im); fl = ImageFont.truetype(SANS_M, 34); fs = ImageFont.truetype(SERIF_B, 40)
    y1 = 720
    spaced(d, (x, y1 - 62), "BEFORE", fl, GOLD, 8); d.text((x + 190, y1 - 70), "イ長調", font=fs, fill=(235, 228, 215))
    im = shadowed(im, a, x, y1, 18)
    d = ImageDraw.Draw(im)
    my = y1 + ch + 70
    d.line((W // 2, my - 40, W // 2, my + 40), fill=GOLD, width=3)
    d.polygon([(W // 2 - 14, my + 30), (W // 2 + 14, my + 30), (W // 2, my + 52)], fill=GOLD)
    y2 = my + 160
    spaced(d, (x, y2 - 62), "AFTER", fl, GOLD, 8); d.text((x + 170, y2 - 70), "ロ長調（＋2）", font=fs, fill=(235, 228, 215))
    im = shadowed(im, b, x, y2, 18)
    return im.convert("RGB")


def end_still():
    im = Image.new("RGB", (W, H), (10, 11, 16))
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse((140, 420, W - 140, 1200), fill=120)
    im = Image.composite(Image.new("RGB", (W, H), (96, 70, 38)), im, g.filter(ImageFilter.GaussianBlur(260))).convert("RGBA")
    icon = os.path.join(ROOT, "icons", "icon-1024.png")
    if os.path.exists(icon):
        im = shadowed(im, Image.open(icon).convert("RGB").resize((260, 260), Image.LANCZOS), (W - 260) // 2, 540, 58)
    d = ImageDraw.Draw(im)
    fw = ImageFont.truetype(SANS_M, 118)
    spaced(d, ((W - slen(d, "CRATE", fw, 22)) / 2, 860), "CRATE", fw, (255, 255, 255), 22)
    fs = ImageFont.truetype(SERIF_L, 50); t = "楽譜を、かんたん移調。"
    d.text(((W - d.textlength(t, font=fs)) / 2, 1020), t, font=fs, fill=(235, 228, 215))
    d.rectangle((W // 2 - 40, 1120, W // 2 + 40, 1121), fill=GOLD)
    ft = ImageFont.truetype(SANS_M, 30); t2 = "FREE  ·  iPhone  ·  iPad"
    spaced(d, ((W - slen(d, t2, ft, 5)) / 2, 1160), t2, ft, GOLD, 5)
    fp = ImageFont.truetype(SANS_M, 40); cta = "App Store で「CRATE 移調」と検索"
    cw = d.textlength(cta, font=fp); px = (W - cw) / 2 - 56
    d.rounded_rectangle((px, 1270, px + cw + 112, 1378), 54, outline=(255, 255, 255), width=2)
    d.text(((W - cw) / 2, 1300), cta, font=fp, fill=(255, 255, 255))
    return im.convert("RGB")


def run(args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def still_part(im, dur, out, tmp, zoom=0.00045):
    p = os.path.join(tmp, os.path.basename(out) + ".png"); im.save(p)
    n = int(dur * 30) + 2
    run(["-loop", "1", "-framerate", "30", "-i", p, "-vf",
         f"scale=1296:2304,zoompan=z='1.0+{zoom}*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30,format=yuv420p,settb=1/30",
         "-frames:v", str(n), "-r", "30", "-c:v", "libx264", "-crf", "16", out])


def clip_part(src, lines, tag, y, dur, out, tmp, ss=0.3):
    ov = os.path.join(tmp, os.path.basename(out) + "_cap.png")
    caption_layer(lines, tag, y, size=80).save(ov)
    run(["-ss", str(ss), "-i", src, "-loop", "1", "-t", str(dur), "-i", ov, "-filter_complex",
         f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},trim=0:{dur},setpts=PTS-STARTPTS,{GRADE}[v];"
         f"[1:v]format=rgba,fade=t=in:st=0.25:d=0.4:alpha=1[o];[v][o]overlay=0:0:shortest=1,fps=30,format=yuv420p,settb=1/30",
         "-an", "-r", "30", "-c:v", "libx264", "-crf", "16", out])


def main():
    fr, reach, music, out = sys.argv[1:5]
    tmp = tempfile.mkdtemp()
    P = lambda n: os.path.join(tmp, n)
    segs = []
    # 1 hook — fully visible from frame 0
    hook = hook_still(fr); still_part(hook, 2.8, P("p0.mp4"), tmp, zoom=0.0003); segs.append((P("p0.mp4"), 2.8))
    # 2 cinematic: shooting the printed score
    clip_part(os.path.join(reach, "cm", "clip1b_clean.mp4"), ["印刷した楽譜を、", "撮るだけ。"], "SHOOT", 1200, 2.6, P("p1.mp4"), tmp); segs.append((P("p1.mp4"), 2.6))
    # 3 real app: transpose
    still_part(phone_still(os.path.join(fr, "fr_c_tp.png"), ["♯ ♭ をタップ。"], "TRANSPOSE"), 1.6, P("p2.mp4"), tmp); segs.append((P("p2.mp4"), 1.6))
    still_part(phone_still(os.path.join(fr, "fr_f_done.png"), ["音符も調号も、", "書き換わる。"], "ANY KEY"), 2.2, P("p3.mp4"), tmp); segs.append((P("p3.mp4"), 2.2))
    # 4 cinematic: singer in their key
    clip_part(os.path.join(reach, "r2", "clip4.mp4"), ["歌う人のキーで、", "そのまま弾ける。"], "PLAY IN THEIR KEY", 1160, 2.6, P("p4.mp4"), tmp, ss=1.0); segs.append((P("p4.mp4"), 2.6))
    # 5 real app: PDF
    still_part(phone_still(os.path.join(fr, "fr_g_pdf.png"), ["PDFで保存して、", "LINEへ。"], "SAVE  ·  SHARE"), 2.0, P("p5.mp4"), tmp); segs.append((P("p5.mp4"), 2.0))
    # 6 end card
    still_part(end_still(), 3.4, P("p6.mp4"), tmp); segs.append((P("p6.mp4"), 3.4))

    inputs = sum((["-i", p] for p, _ in segs), [])
    fc, prev, off = "", "[0:v]", 0.0
    for k in range(1, len(segs)):
        off += segs[k - 1][1] - XF
        lbl = f"[x{k}]"
        trans = "fadeblack" if k == len(segs) - 1 else "fade"
        fc += f"{prev}[{k}:v]xfade=transition={trans}:duration={XF}:offset={off:.2f}{lbl};"
        prev = lbl
    total = off + segs[-1][1]
    fc += f"{prev}fade=t=out:st={total-0.6:.2f}:d=0.6[v];"
    fc += f"[{len(segs)}:a]atrim=0:{total:.2f},asetpts=PTS-STARTPTS,afade=t=out:st={total-1.6:.2f}:d=1.6,loudnorm=I=-16:TP=-1.5:LRA=9[a]"
    run([*inputs, "-i", music, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out])
    hook.save(os.path.splitext(out)[0] + "_cover.jpg", quality=92)
    print("wrote", out, f"{total:.2f}s")


if __name__ == "__main__":
    main()
