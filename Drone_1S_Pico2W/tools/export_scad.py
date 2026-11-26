#!/usr/bin/python3
"""
Export the KiCad boards to an OpenSCAD include, so the 3D model of the drone
(OpenScad-Designs/Drones/1S_PiZero) shows the real board outline and the real
component placement. Run after gen_pcb.py:

    /usr/bin/python3 export_scad.py [out.scad]

Default output: ../../../OpenScad-Designs/Drones/1S_PiZero/1S_PiZero_electronics.scad
(the sibling checkout), else ../build/1S_PiZero_electronics.scad.

Everything is in scad coordinates (x forward, y left, mm, origin = frame centre).
Parts are exported by their pads, so the scad side derives orientation from pad
positions and never needs KiCad's rotation / flip conventions:

    kc_<board>_parts = [[ref, footprint, side, [[pad, x, y, drill], ...]], ...]
    side: "top" or "bottom"
"""

import math
import os
import subprocess
import sys

import pcbnew

from design import FC, FRAME, B2B, ORIGIN_X, ORIGIN_Y, REVISION

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SIBLING = os.path.normpath(os.path.join(ROOT, "..", "..", "OpenScad-Designs", "Drones", "1S_PiZero"))


def sc(v):
    """KiCad VECTOR2I -> scad [x, y]."""
    return (round(pcbnew.ToMM(v.x) - ORIGIN_X, 4), round(ORIGIN_Y - pcbnew.ToMM(v.y), 4))


def outline(board):
    """Board outline as one closed polygon (segments + arcs, arcs sampled every ~10 deg)."""
    segs = []
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        if d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            segs.append([sc(d.GetStart()), sc(d.GetEnd())])
        elif d.GetShape() == pcbnew.SHAPE_T_ARC:
            a, m, b = sc(d.GetStart()), sc(d.GetArcMid()), sc(d.GetEnd())
            c = sc(d.GetCenter())
            r = math.hypot(a[0] - c[0], a[1] - c[1])
            t0 = math.atan2(a[1] - c[1], a[0] - c[0])
            tm = math.atan2(m[1] - c[1], m[0] - c[0])
            t1 = math.atan2(b[1] - c[1], b[0] - c[0])
            # sweep through the mid point
            def norm(t): return (t - t0) % (2 * math.pi)
            sweep = norm(t1) if norm(tm) < norm(t1) else norm(t1) - 2 * math.pi
            n = max(2, int(abs(sweep) / math.radians(10)))
            pts = [(round(c[0] + r * math.cos(t0 + sweep * i / n), 4),
                    round(c[1] + r * math.sin(t0 + sweep * i / n), 4)) for i in range(n + 1)]
            pts[0], pts[-1] = a, b
            segs.append(pts)
    # chain the pieces end to end
    key = lambda p: (round(p[0], 3), round(p[1], 3))
    poly = list(segs.pop(0))
    while segs:
        for i, s in enumerate(segs):
            if key(s[0]) == key(poly[-1]):
                poly += s[1:]
            elif key(s[-1]) == key(poly[-1]):
                poly += s[::-1][1:]
            else:
                continue
            segs.pop(i)
            break
        else:
            raise RuntimeError("outline does not close")
    if key(poly[0]) == key(poly[-1]):
        poly.pop()
    return poly


def parts(board, skip=()):
    out = []
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        if any(ref.startswith(s) for s in skip):
            continue
        pads = []
        for p in sorted(fp.Pads(), key=lambda p: (p.GetNumber().isdigit() and int(p.GetNumber()) or 0)):
            x, y = sc(p.GetPosition())
            pads.append((p.GetNumber(), x, y, round(pcbnew.ToMM(p.GetDrillSize().x), 3)))
        side = "bottom" if fp.IsFlipped() else "top"
        out.append((ref, fp.GetFPID().GetLibItemName().wx_str(), side, pads))
    return out


def fmt_parts(name, ps):
    lines = [f"{name} = ["]
    for ref, fpn, side, pads in ps:
        pp = ", ".join(f'["{n}", {x:g}, {y:g}, {d:g}]' for n, x, y, d in pads)
        lines.append(f'    ["{ref}", "{fpn}", "{side}", [{pp}]],')
    lines.append("];")
    return "\n".join(lines)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else (
        os.path.join(SIBLING, "1S_PiZero_electronics.scad") if os.path.isdir(SIBLING)
        else os.path.join(ROOT, "build", "1S_PiZero_electronics.scad"))
    fr = pcbnew.LoadBoard(os.path.join(ROOT, "Frame", FRAME["project"] + ".kicad_pcb"))
    fc = pcbnew.LoadBoard(os.path.join(ROOT, "FC", FC["project"] + ".kicad_pcb"))
    try:
        rev = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True,
                             text=True).stdout.strip()
    except OSError:
        rev = "?"
    fc_poly = outline(fc)
    txt = f"""// GENERATED - do not edit. Source: KiCad-Designs/Drone_1S_Pico2W (rev {REVISION}, git {rev}),
// tools/export_scad.py, from Frame/{FRAME['project']}.kicad_pcb and FC/{FC['project']}.kicad_pcb.
// scad coordinates: x forward, y left, mm, origin at the frame centre.
// Parts: [ref, footprint, side ("top"/"bottom" of that board), [[pad, x, y, drill], ...]].

kc_frame_t = {FRAME['thickness']:g};     // frame PCB thickness
kc_fc_t    = {FC['thickness']:g};     // FC module PCB thickness
kc_b2b_standoff = {B2B['standoff']:g}; // FC top to frame bottom = landing gear + M2 standoff = mated header + socket

kc_gear_t  = {B2B['gear_t']:g};  // printed landing gear clamped between frame and the FC standoffs
kc_fc_size = [{max(p[0] for p in fc_poly) - min(p[0] for p in fc_poly):.2f}, {max(p[1] for p in fc_poly) - min(p[1] for p in fc_poly):.2f}];  // outline bounding box x, y
kc_fc_outline = [{", ".join(f"[{x:g}, {y:g}]" for x, y in fc_poly)}];

{fmt_parts("kc_fc_parts", parts(fc))}

// frame parts placed in KiCad that the scad does not already draw (ESC pads,
// motor holes and battery pads come from the scad itself)
{fmt_parts("kc_frame_parts", parts(fr, skip=("H", "J1", "J2", "J3", "J4", "BT")))}
"""
    with open(out, "w") as f:
        f.write(txt)
    print(f"wrote {out}: FC outline {len(fc_poly)} points, "
          f"{len(parts(fc))} FC parts, {len(parts(fr, skip=('H', 'J1', 'J2', 'J3', 'J4', 'BT')))} frame parts")


if __name__ == "__main__":
    main()
