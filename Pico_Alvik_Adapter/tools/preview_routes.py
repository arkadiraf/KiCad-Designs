#!/usr/bin/env python3
"""Quick PNG preview of build/geometry.json + build/routes.json (debug aid)."""
import json
import os
import sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(os.path.dirname(HERE), "build")
S = 20  # px per mm

g = json.load(open(os.path.join(B, "geometry.json")))
r = json.load(open(os.path.join(B, "routes.json"))) if os.path.exists(os.path.join(B, "routes.json")) else {"tracks": [], "vias": []}
xs = [p[0] for p in g["outline"]]
ys = [p[1] for p in g["outline"]]
x0, y0 = min(xs) - 1, min(ys) - 1
W, H = int((max(xs) - x0 + 1) * S), int((max(ys) - y0 + 1) * S)
im = Image.new("RGB", (W, H), (20, 20, 20))
d = ImageDraw.Draw(im, "RGBA")
P = lambda x, y: ((x - x0) * S, (y - y0) * S)
d.polygon([P(*p) for p in g["outline"]], outline=(220, 220, 0), fill=(0, 40, 0))
for k in g["keepouts"]:
    d.polygon([P(*p) for p in k["pts"]], outline=(255, 0, 255))
col = {"F": (220, 40, 40, 170), "B": (40, 120, 255, 170)}
for p in g["pads"]:
    for l in p["layers"]:
        b = p["bbox"]
        d.rectangle([P(b[0], b[1]), P(b[2], b[3])], fill=col[l][:3] + (110,), outline=(255, 255, 255, 120))
for t in r["tracks"]:
    d.line([P(t["x1"], t["y1"]), P(t["x2"], t["y2"])], fill=col[t["layer"]], width=max(1, int(t["w"] * S)))
for v in r["vias"]:
    x, y = P(v["x"], v["y"])
    rr = v["d"] / 2 * S
    d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(200, 200, 200), outline=(0, 0, 0))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(B, "routes_preview.png")
im.save(out)
print(out)
