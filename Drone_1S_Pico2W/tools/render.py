#!/usr/bin/env python3
"""Render docs/*.png from the boards with kicad-cli + cairosvg (run from tools/)."""
import os, subprocess
import cairosvg
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")
os.makedirs(B, exist_ok=True)


def svg(pcb, layers, out, mirror=False):
    cmd = ["kicad-cli", "pcb", "export", "svg", "--exclude-drawing-sheet", "-l", layers, "-o", out, pcb]
    if mirror:
        cmd.insert(4, "-m")
    subprocess.run(cmd, check=True, capture_output=True)
    png = out[:-4] + ".png"
    cairosvg.svg2png(url=out, write_to=png, output_width=6000, background_color="white")
    im = Image.open(png)
    return im.crop(im.convert("L").point(lambda v: v < 250 and 255).getbbox())


def sheet(ims, labels, out, height=None):
    if height:
        ims = [i.resize((int(i.width * height / i.height), height)) for i in ims]
    w = sum(i.width for i in ims) + 80 * (len(ims) - 1)
    o = Image.new("RGB", (w, max(i.height for i in ims) + 50), "white")
    d, x = ImageDraw.Draw(o), 0
    for i, l in zip(ims, labels):
        o.paste(i, (x, 50))
        d.text((x + 10, 10), l, fill="black")
        x += i.width + 80
    o.save(os.path.join(ROOT, "docs", out))


fc = os.path.join(ROOT, "FC", "Drone_1S_FC.kicad_pcb")
fr = os.path.join(ROOT, "Frame", "Drone_1S_Frame.kicad_pcb")
top = svg(fc, "Edge.Cuts,F.Cu,F.Silkscreen,F.Fab,Dwgs.User", os.path.join(B, "fc_top.svg"))
bot = svg(fc, "Edge.Cuts,B.Cu,B.Silkscreen,B.Fab,Cmts.User", os.path.join(B, "fc_bot.svg"), mirror=True)
sheet([top, bot], ["FC TOP (Pico 2 W + J1/J2 male headers up to the frame)",
                   "FC BOTTOM, mirrored view from below (deck P1/P2 + ICs)"], "fc_stage1.png")
ftop = svg(fr, "Edge.Cuts,F.Cu,F.Silkscreen,Dwgs.User", os.path.join(B, "frame_top.svg"))
fbot = svg(fr, "Edge.Cuts,B.Cu,B.Silkscreen,B.Fab,Cmts.User", os.path.join(B, "frame_bot.svg"), mirror=True)
sheet([ftop, fbot], ["FRAME TOP", "FRAME BOTTOM, mirrored view from below (J5/J6 sockets for the FC, ESCs)"],
      "frame_stage1.png", height=1600)
print("rendered docs/fc_stage1.png docs/frame_stage1.png")
