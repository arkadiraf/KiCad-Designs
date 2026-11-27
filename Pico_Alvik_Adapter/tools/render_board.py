#!/usr/bin/env python3
"""Photo-style 2D renders of the PCB (top, bottom, top with Pico W fitted).

Each layer is exported from KiCad as a full-page monochrome SVG, rasterised,
and composited with solder-mask / copper / silkscreen colours.
Writes fabrication/docs/Pico_Alvik_Adapter_render.png
"""
import io
import os
import subprocess
import tempfile

import shutil

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
PCB = os.path.join(PRJ, "Pico_Alvik_Adapter.kicad_pcb")
OUT = os.path.join(PRJ, "fabrication", "docs", "Pico_Alvik_Adapter_render.png")

PX = 30                      # px per mm
PAGE_W = 297.0               # A4 landscape page used by the board
BX0, BY0, BX1, BY1 = 98.0, 97.0, 126.0, 153.0   # crop window (page mm)

MASK = np.array([18, 92, 48])        # green solder mask over bare FR4
MASK_CU = np.array([40, 128, 62])    # mask over copper (lighter)
GOLD = np.array([212, 172, 84])      # ENIG pads
SILK = np.array([245, 245, 240])
BG = (34, 36, 40)


KICAD_CLI = (os.environ.get("KICAD_CLI") or shutil.which("kicad-cli")
             or r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
_VER = subprocess.run([KICAD_CLI, "version"], capture_output=True, text=True).stdout.strip()
SVG_MODE = ["--mode-single"] if int((_VER or "7").split(".")[0]) >= 9 else []


def font(*names, size):
    """First available TrueType font (DejaVu on Linux, Arial on Windows)."""
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


def svg_to_png(svg, width):
    """SVG -> PNG bytes on a white background (cairosvg, else PyMuPDF)."""
    try:
        import cairosvg
        return cairosvg.svg2png(url=svg, output_width=width, background_color="white")
    except ImportError:
        import fitz
        page = fitz.open(svg)[0]
        z = width / page.rect.width
        return page.get_pixmap(matrix=fitz.Matrix(z, z), alpha=False).tobytes("png")


def layer(name, tmp):
    svg = os.path.join(tmp, name.replace(".", "_") + ".svg")
    subprocess.run([KICAD_CLI, "pcb", "export", "svg", "--layers", name,
                    "--black-and-white", "--exclude-drawing-sheet",
                    "--page-size-mode", "0", *SVG_MODE, "-o", svg, PCB],
                   check=True, capture_output=True)
    png = svg_to_png(svg, int(PAGE_W * PX))
    im = np.asarray(Image.open(io.BytesIO(png)).convert("L"))
    x0, y0, x1, y1 = (int(v * PX) for v in (BX0, BY0, BX1, BY1))
    return im[y0:y1, x0:x1] < 128          # True where the layer has ink


def board_mask(edge):
    edge = ndimage.binary_dilation(edge, iterations=2)
    outside = ndimage.binary_fill_holes(~edge) ^ ~edge   # holes = inside regions
    inside = ndimage.binary_fill_holes(edge) & ~edge
    return ndimage.binary_dilation(inside | (edge & ndimage.binary_dilation(inside, iterations=3)), iterations=1)


def compose(side, L):
    cu, mask_open, silk = L[f"{side}.Cu"], L[f"{side}.Mask"], L[f"{side}.Silkscreen"]
    board = L["board"]
    img = np.zeros(cu.shape + (3,), float)
    img[:] = BG
    img[board] = MASK
    img[board & cu] = MASK_CU
    img[board & cu & mask_open] = GOLD
    img[board & ~cu & mask_open] = (170, 150, 100)      # bare FR4 if any
    img[board & silk & ~mask_open] = SILK
    # subtle shading on copper edges
    edge = cu ^ ndimage.binary_erosion(cu, iterations=1)
    img[board & edge & ~mask_open] *= 0.85
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    if side == "B":
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im


def mm(x, y):
    return ((x - BX0) * PX, (y - BY0) * PX)


def draw_pico(im):
    """Simplified Raspberry Pi Pico W on top of the board (51 x 21 mm)."""
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    cx, cy = 112.0, 125.5
    # shadow
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([mm(cx - 10.2, cy - 25.0), mm(cx + 10.9, cy + 25.9)],
                                         radius=PX, fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(PX * 0.5))
    ov = Image.alpha_composite(ov, sh)
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle([mm(cx - 10.5, cy - 25.5), mm(cx + 10.5, cy + 25.5)],
                        radius=int(PX * 0.6), fill=(22, 110, 70, 255))
    # castellations
    for k in range(20):
        y = cy - 24.13 + 2.54 * k
        for sx in (-1, 1):
            x = cx + sx * 9.69
            d.ellipse([mm(x - 0.6 + sx * 0.25, y - 0.6), mm(x + 0.6 + sx * 0.25, y + 0.6)],
                      fill=(220, 180, 90, 255))
            x2 = cx + sx * 10.5
            d.pieslice([mm(x2 - 0.55, y - 0.55), mm(x2 + 0.55, y + 0.55)],
                       90 if sx > 0 else 270, 270 if sx > 0 else 90, fill=(30, 30, 30, 255))
            d.ellipse([mm(cx + sx * 8.89 - 0.5, y - 0.5), mm(cx + sx * 8.89 + 0.5, y + 0.5)],
                      fill=(200, 165, 80, 255), outline=(15, 70, 45, 255))
    # mounting holes
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = cx + sx * 5.7, cy + sy * 23.5
            d.ellipse([mm(x - 1.4, y - 1.4), mm(x + 1.4, y + 1.4)], fill=(210, 175, 85, 255))
            d.ellipse([mm(x - 1.05, y - 1.05), mm(x + 1.05, y + 1.05)], fill=BG + (255,))
    # micro USB (overhangs 1.3 mm)
    d.rectangle([mm(cx - 4.0, cy - 26.8), mm(cx + 4.0, cy - 21.6)], fill=(190, 192, 196, 255),
                outline=(120, 120, 125, 255), width=2)
    d.rectangle([mm(cx - 3.0, cy - 26.8), mm(cx + 3.0, cy - 26.0)], fill=(60, 60, 65, 255))
    # BOOTSEL button
    d.rectangle([mm(cx - 6.2, cy - 17.0), mm(cx - 2.6, cy - 13.4)], fill=(230, 230, 230, 255))
    d.ellipse([mm(cx - 5.4, cy - 16.2), mm(cx - 3.4, cy - 14.2)], fill=(200, 200, 205, 255))
    # RP2040
    d.rectangle([mm(cx - 3.5, cy - 7.0), mm(cx + 3.5, cy + 0.0)], fill=(25, 25, 28, 255))
    # flash, crystal, passives
    d.rectangle([mm(cx - 3.0, cy - 13.0), mm(cx + 2.5, cy - 9.0)], fill=(30, 30, 32, 255))
    for i in range(6):
        d.rectangle([mm(cx + 4.0, cy - 12 + i * 1.6), mm(cx + 5.0, cy - 11.4 + i * 1.6)], fill=(150, 120, 80, 255))
    # debug header holes
    for k in range(3):
        x = cx + 0.584 + 2.54 * k
        d.ellipse([mm(x - 0.75, cy + 5.7 - 0.75), mm(x + 0.75, cy + 5.7 + 0.75)], fill=(210, 175, 85, 255))
        d.ellipse([mm(x - 0.45, cy + 5.7 - 0.45), mm(x + 0.45, cy + 5.7 + 0.45)], fill=BG + (255,))
    # CYW43439 shield can
    d.rectangle([mm(cx - 5.2, cy + 8.0), mm(cx + 5.2, cy + 16.0)], fill=(200, 202, 206, 255),
                outline=(150, 150, 155, 255), width=2)
    # antenna area
    d.rectangle([mm(cx - 6.5, cy + 18.0), mm(cx + 6.5, cy + 24.3)], outline=(200, 170, 80, 255), width=3)
    try:
        f = font("DejaVuSans-Bold.ttf", "arialbd.ttf", size=int(PX * 0.95))
        txt = Image.new("RGBA", (int(PX * 30), int(PX * 2)), (0, 0, 0, 0))
        ImageDraw.Draw(txt).text((0, 0), "Raspberry Pi Pico W", font=f, fill=(235, 235, 235, 255))
        txt = txt.rotate(90, expand=True)
        txt = txt.crop(txt.getbbox())
        ov.alpha_composite(txt, (int(mm(cx - 7.9, 0)[0]), int(mm(0, cy + 1.0)[1])))
    except OSError:
        pass
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def draw_headers(im):
    """Two 1x15 SMD male headers (bottom side; rows are symmetric so mirroring is moot)."""
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    d = ImageDraw.Draw(ov)
    y0, y1 = 104.14 - 1.27, 139.70 + 1.27
    for x in (104.38, 119.62):
        ds.rectangle([mm(x - 1.27 + 0.4, y0 + 0.5), mm(x + 1.27 + 0.4, y1 + 0.5)], fill=(0, 0, 0, 130))
    sh = sh.filter(ImageFilter.GaussianBlur(PX * 0.4))
    for x in (104.38, 119.62):
        d.rectangle([mm(x - 1.27, y0), mm(x + 1.27, y1)], fill=(28, 28, 30, 255))
        for k in range(15):
            y = 104.14 + 2.54 * k
            d.line([mm(x - 1.27, y + 1.27), mm(x + 1.27, y + 1.27)], fill=(55, 55, 58, 255), width=2)
            d.rectangle([mm(x - 0.42, y - 0.42), mm(x + 0.42, y + 0.42)], fill=(225, 190, 95, 255))
            d.rectangle([mm(x - 0.42, y - 0.42), mm(x + 0.42, y - 0.2)], fill=(250, 225, 140, 255))
    out = Image.alpha_composite(im.convert("RGBA"), sh)
    return Image.alpha_composite(out, ov).convert("RGB")


def label(im, text):
    pad = 70
    out = Image.new("RGB", (im.width, im.height + pad), BG)
    out.paste(im, (0, pad))
    d = ImageDraw.Draw(out)
    f = font("DejaVuSans.ttf", "arial.ttf", size=34)
    w = d.textlength(text, font=f)
    d.text(((im.width - w) / 2, 18), text, font=f, fill=(230, 230, 230))
    return out


def find_coeffs(dst, src):
    """Perspective coefficients mapping output (dst) points to input (src) points."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def angled(im, board, thick_px=26, tilt=0.30, skew=0.18):
    """Pseudo-3D view: tilt the board back, add PCB edge thickness and a shadow."""
    w, h = im.size
    rgba = im.convert("RGBA")
    alpha = Image.fromarray((board * 255).astype(np.uint8))
    if alpha.size != im.size:
        alpha = alpha.resize(im.size)
    rgba.putalpha(alpha)
    # output quad (top edge narrower -> perspective)
    W, H = int(w * 1.5), int(h * 0.95)
    ox, oy = int(W * 0.18), int(H * 0.08)
    top_w = w * (1 - skew)
    dst = [(ox + (w - top_w) / 2 + w * 0.10, oy), (ox + (w + top_w) / 2 + w * 0.10, oy),
           (ox + w, oy + h * (1 - tilt)), (ox, oy + h * (1 - tilt))]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    co = find_coeffs(dst, src)
    face = rgba.transform((W, H), Image.PERSPECTIVE, co, Image.BICUBIC)
    a = np.asarray(face)[:, :, 3] > 40
    canvas = Image.new("RGBA", (W, H), BG + (255,))
    sh = Image.fromarray((a * 150).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.putalpha(ImageChops.offset(sh, 30, 45))
    canvas = Image.alpha_composite(canvas, shadow)
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ea = Image.fromarray((a * 255).astype(np.uint8))
    for k in range(thick_px, 0, -1):
        layer_c = Image.new("RGBA", (W, H), (178, 160, 110, 255) if k > 3 else (14, 70, 36, 255))
        layer_c.putalpha(ImageChops.offset(ea, 0, k))
        edge = Image.alpha_composite(edge, layer_c)
    canvas = Image.alpha_composite(canvas, edge)
    canvas = Image.alpha_composite(canvas, face)
    return canvas.convert("RGB").crop(Image.fromarray((np.asarray(canvas.convert("L")) != BG[0]).astype(np.uint8) * 255).getbbox())


def main():
    with tempfile.TemporaryDirectory() as tmp:
        L = {n: layer(n, tmp) for n in ("F.Cu", "B.Cu", "F.Mask", "B.Mask",
                                        "F.Silkscreen", "B.Silkscreen", "Edge.Cuts")}
    edge = ndimage.binary_dilation(L["Edge.Cuts"], iterations=2)
    L["board"] = ndimage.binary_fill_holes(edge)
    top = compose("F", L)
    bottom = compose("B", L)
    fitted = draw_pico(top)
    bottom_hdr = draw_headers(bottom)
    panels = [label(top, "Top (bare board)"), label(fitted, "Top with Pico W fitted"),
              label(bottom, "Bottom (bare)"), label(bottom_hdr, "Bottom with Nano headers")]
    gap = 40
    W = sum(p.width for p in panels) + gap * (len(panels) + 1)
    H = max(p.height for p in panels) + gap * 2
    sheet = Image.new("RGB", (W, H), BG)
    x = gap
    for p in panels:
        sheet.paste(p, (x, gap))
        x += p.width + gap
    sheet.save(OUT)
    print(OUT, sheet.size)
    d = os.path.dirname(OUT)
    top.save(os.path.join(d, "render_top.png"))
    bottom.save(os.path.join(d, "render_bottom.png"))
    bottom_hdr.save(os.path.join(d, "render_bottom_with_headers.png"))
    fitted.save(os.path.join(d, "render_top_with_pico.png"))
    # angled views (pico: board outline incl. USB overhang via non-background pixels)
    fit_mask = np.asarray(fitted.convert("RGB")).astype(int)
    fit_mask = np.abs(fit_mask - np.array(BG)).sum(axis=2) > 10
    a1 = angled(fitted, fit_mask)
    a2 = angled(bottom_hdr, np.abs(np.asarray(bottom_hdr.convert("RGB")).astype(int) - np.array(BG)).sum(axis=2) > 10)
    a1.save(os.path.join(d, "render_angled_top.png"))
    a2.save(os.path.join(d, "render_angled_bottom.png"))
    g = 40
    pair = Image.new("RGB", (a1.width + a2.width + 3 * g, max(a1.height, a2.height) + 2 * g), BG)
    pair.paste(a1, (g, g)); pair.paste(a2, (a1.width + 2 * g, g))
    pair.save(os.path.join(d, "Pico_Alvik_Adapter_render_angled.png"))
    print("angled renders written")


if __name__ == "__main__":
    main()
