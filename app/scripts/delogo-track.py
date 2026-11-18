#!/usr/bin/env python3
"""Track a small logo with multi-scale template matching and inpaint it away on every frame.
usage: delogo-track.py in.mp4 out.mp4 ref_time x0 y0 x1 y1 [debug_dir]
(x0,y0,x1,y1) = logo box on the frame at ref_time (source pixels).
"""
import os, subprocess, sys
import cv2, numpy as np

src, out, rt = sys.argv[1], sys.argv[2], float(sys.argv[3])
x0, y0, x1, y1 = map(int, sys.argv[4:8])
dbg = sys.argv[8] if len(sys.argv) > 8 else None
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frames = []
while True:
    ok, f = cap.read()
    if not ok: break
    frames.append(f)
ri = min(int(round(rt * fps)), len(frames) - 1)
g = lambda f: cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
tpl = g(frames[ri])[y0:y1, x0:x1]
th, tw = tpl.shape
H, W = frames[0].shape[:2]


def match(gray, center=None, scale=None):
    best = (-1, None)
    scales = np.linspace(0.45, 1.6, 47) if scale is None else np.linspace(scale * 0.9, scale * 1.1, 9)
    for s in scales:
        t = cv2.resize(tpl, (max(8, int(tw * s)), max(8, int(th * s))))
        if center is None:
            area, ox, oy = gray, 0, 0
        else:
            r = int(max(t.shape) * 3); cx, cy = center
            ax0, ay0 = max(0, cx - r), max(0, cy - r); ax1, ay1 = min(W, cx + r), min(H, cy + r)
            area, ox, oy = gray[ay0:ay1, ax0:ax1], ax0, ay0
        if area.shape[0] < t.shape[0] or area.shape[1] < t.shape[1]: continue
        res = cv2.matchTemplate(area, t, cv2.TM_CCOEFF_NORMED)
        _, mv, _, ml = cv2.minMaxLoc(res)
        if mv > best[0]:
            best = (mv, (ml[0] + ox, ml[1] + oy, t.shape[1], t.shape[0], s))
    return best


boxes = [None] * len(frames)
# track forward and backward from the reference frame
for rng in (range(ri, len(frames)), range(ri, -1, -1)):
    c, sc = None, None
    for i in rng:
        v, b = match(g(frames[i]), c, sc)
        if (b is None or v < 0.45) and c is not None:
            v, b = match(g(frames[i]))  # re-acquire globally
        if b is not None and v >= 0.45:
            boxes[i] = b; c = (b[0] + b[2] // 2, b[1] + b[3] // 2); sc = b[4]
        else:
            c, sc = None, None
# fill gaps by holding the nearest box (logo cannot vanish between two detections)
last = None
for i in range(len(boxes)):
    if boxes[i] is None and last is not None: boxes[i] = last
    if boxes[i] is not None: last = boxes[i]
print("tracked", sum(b is not None for b in boxes), "/", len(boxes))

proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps),
                         "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "15", "-pix_fmt", "yuv420p", out],
                        stdin=subprocess.PIPE)
for i, f in enumerate(frames):
    b = boxes[i]
    if b is not None:
        x, y, w, h, _ = b
        px, py = int(w * 0.35) + 3, int(h * 0.35) + 3
        m = np.zeros((H, W), np.uint8)
        cv2.rectangle(m, (max(0, x - px), max(0, y - py)), (min(W - 1, x + w + px), min(H - 1, y + h + py)), 255, -1)
        f = cv2.inpaint(f, m, 5, cv2.INPAINT_TELEA)
        if dbg and i % 12 == 0:
            d = f.copy(); cv2.rectangle(d, (x - px, y - py), (x + w + px, y + h + py), (0, 255, 255), 2)
            cv2.imwrite(os.path.join(dbg, f"d_{i:03d}.png"), d)
    proc.stdin.write(f.tobytes())
proc.stdin.close(); proc.wait()
print("wrote", out)
