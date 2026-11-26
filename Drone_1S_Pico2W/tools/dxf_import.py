"""
Read the OpenSCAD DXF of the frame outline (LWPOLYLINE contours only, which is
all OpenSCAD writes) and classify the contours:

* the largest contour is the board outline,
* every other contour is a polygonised circle: fit centre + diameter and snap
  the diameter to design.HOLE_CLASSES.

Run directly to print a summary and cross-check against the scad parameters:
    python3 dxf_import.py [file.dxf]
"""

import math
import os
import sys

from design import HOLE_CLASSES

HERE = os.path.dirname(os.path.abspath(__file__))
DXF = os.path.join(HERE, "..", "Materials", "extracted", "1S_PiZero_PCB_outline.dxf")


def read_polylines(path):
    """LWPOLYLINE contours (newer OpenSCAD) or LINE segments chained into
    closed contours (OpenSCAD 2021.01)."""
    with open(path) as f:
        lines = [l.strip() for l in f]
    pairs = list(zip(lines[0::2], lines[1::2]))
    polys, segs, cur, kind, xy = [], [], None, None, {}
    for code, val in pairs + [("0", "EOF")]:
        if code == "0":
            if kind == "LWPOLYLINE":
                polys.append(cur)
            elif kind == "LINE":
                segs.append(((xy["10"], xy["20"]), (xy["11"], xy["21"])))
            kind, cur, xy = val, [], {}
        elif kind == "LWPOLYLINE":
            if code == "10":
                x = float(val)
            elif code == "20":
                cur.append((x, float(val)))
        elif kind == "LINE" and code in ("10", "20", "11", "21"):
            xy[code] = float(val)
    key = lambda p: (round(p[0], 4), round(p[1], 4))
    nxt = {key(a): b for a, b in segs}
    seen = set()
    for a, _ in segs:
        if key(a) in seen:
            continue
        poly, p = [], a
        while key(p) not in seen:
            seen.add(key(p))
            poly.append(p)
            p = nxt[key(p)]
        polys.append(poly)
    return [p for p in polys if len(p) >= 3]


def area(p):
    return 0.5 * sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))


def fit_circle(p):
    cx = sum(q[0] for q in p) / len(p)
    cy = sum(q[1] for q in p) / len(p)
    r = [math.hypot(q[0] - cx, q[1] - cy) for q in p]
    return cx, cy, 2 * sum(r) / len(r), (max(r) - min(r))


def load(path=DXF):
    polys = read_polylines(path)
    polys.sort(key=lambda p: -abs(area(p)))
    outline, holes = polys[0], []
    for p in polys[1:]:
        cx, cy, d, spread = fit_circle(p)
        nominal = min(HOLE_CLASSES, key=lambda k: abs(k - d))
        # OpenSCAD polygons are inscribed: vertex radius = nominal radius
        if abs(nominal - d) > 0.05 or spread > 0.01:
            raise ValueError(f"contour at ({cx:.2f},{cy:.2f}) d={d:.3f} is not a known hole")
        holes.append(dict(x=round(cx, 4), y=round(cy, 4), d=nominal, kind=HOLE_CLASSES[nominal]))
    return outline, holes


if __name__ == "__main__":
    outline, holes = load(sys.argv[1] if len(sys.argv) > 1 else DXF)
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    print(f"outline: {len(outline)} vertices, bbox x {min(xs):.3f}..{max(xs):.3f} "
          f"y {min(ys):.3f}..{max(ys):.3f}, area {abs(area(outline)):.1f} mm^2")
    from collections import Counter
    for (kind, d), n in sorted(Counter((h["kind"], h["d"]) for h in holes).items()):
        print(f"  {n:3d} x {kind:12s} d={d}")
