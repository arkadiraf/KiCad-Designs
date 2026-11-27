#!/usr/bin/env python3
"""Board: outline, mounting holes, guides, and (stage 3) every footprint placed with its nets. Run with KiCad's Python:

    "C:/Program Files/KiCad/10.0/bin/python.exe" gen_pcb.py

Writes ../PicoBalancer.kicad_pcb (+ .kicad_pro if missing) and checks every hole against the DXF.
Guides (not fabricated): Dwgs.User = holders, holder channel, Pico, encoder zone; Cmts.User = hole keep-outs.
"""
import json
import os
import re
import sys

import pcbnew

from design import (BOARD_H, BOARD_W, BT_POS, ENCODER_ZONE, HOLDER, HOLDER_CHANNEL, HOLE_D, HOLE_KEEPOUT,
                    HOLES, PROJECT, REVISION, DATE, SHARED_LIBS, ZONES, BOLT_KEEPOUT_R, HOLDER_HOLES, CLAMP_HOLES, COVER_PILLAR, to_kicad,
                    BOM, DNP, PLACEMENT, VALUES, build_nets)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, f"{PROJECT}.kicad_pcb")
PRO = os.path.join(ROOT, f"{PROJECT}.kicad_pro")
DXF = os.path.join(ROOT, "Materials", "extracted", "PicoBalancer_PCB.dxf")
MM = pcbnew.FromMM


def pt(x, y):
    kx, ky = to_kicad(x, y)
    return pcbnew.VECTOR2I(MM(kx), MM(ky))


def rect(board, x0, y0, x1, y1, layer, w=0.1):
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(*a))
        s.SetEnd(pt(*b))
        s.SetLayer(layer)
        s.SetWidth(MM(w))
        board.Add(s)


def text(board, s, x, y, layer, size=1.5):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(pt(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(max(0.15, size * 0.15)))
    board.Add(t)
    return t


LIB_MECH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), SHARED_LIBS, "KD_Mechanical.pretty"))
HOLE_FP = f"MountingHole_{HOLE_D}mm_NPTH"


def write_hole_fp():
    os.makedirs(LIB_MECH, exist_ok=True)
    with open(os.path.join(LIB_MECH, HOLE_FP + ".kicad_mod"), "w") as f:
        f.write(f"""(footprint "{HOLE_FP}"
  (version 20240108)
  (generator "PicoBalancer_gen_pcb")
  (layer "F.Cu")
  (descr "NPTH {HOLE_D} mm (M2.5 clearance), from the PicoBalancer DXF")
  (attr exclude_from_pos_files exclude_from_bom)
  (property "Reference" "REF**" (at 0 -2.5 0) (layer "F.SilkS") (hide yes)
    (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "{HOLE_FP}" (at 0 2.5 0) (layer "F.Fab") (hide yes)
    (effects (font (size 1 1) (thickness 0.15))))
  (fp_circle (center 0 0) (end {HOLE_D / 2 + 0.25:.3f} 0) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))
  (pad "" np_thru_hole circle (at 0 0) (size {HOLE_D} {HOLE_D}) (drill {HOLE_D}) (layers "*.Cu" "*.Mask"))
)
""")


def hole(board, ref, x, y):
    fp = pcbnew.FootprintLoad(LIB_MECH, HOLE_FP)
    fp.SetFPID(pcbnew.LIB_ID("KD_Mechanical", HOLE_FP))
    fp.SetReference(ref)
    fp.SetPosition(pt(x, y))
    board.Add(fp)


def dxf_circles():
    """(x, y_board, d) of every CIRCLE in the DXF; DXF y -> board y = -(y + 121)."""
    lines = [l.strip() for l in open(DXF)]
    out = []
    for i, l in enumerate(lines):
        if l == "CIRCLE" and lines[i - 1] == "0":
            kv, j = {}, i + 1
            while j < len(lines) - 1 and lines[j] != "0":
                kv[lines[j]] = lines[j + 1]
                j += 2
            out.append((float(kv["10"]), -(float(kv["20"]) + 121.0), 2 * float(kv["40"])))
    return out


KD_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), SHARED_LIBS))
STOCK_FP = next(p for p in ("C:/Program Files/KiCad/10.0/share/kicad/footprints", "/usr/share/kicad/footprints")
                if os.path.isdir(p))


def place_parts(board):
    """Load every BOM footprint (except bought-only lines), place it per design.PLACEMENT and assign pad nets."""
    netmap = {}
    for net, conns in build_nets().items():
        for r, p in conns:
            netmap[(r, p)] = net
    nets = {}
    for net in sorted(set(netmap.values())):
        ni = pcbnew.NETINFO_ITEM(board, net)
        board.Add(ni)
        nets[net] = ni
    placed, missing_pads = 0, []
    for refs, val, sym, fpid, _role in BOM:
        if sym == "-":
            continue
        lib, name = fpid.split(":")
        path = os.path.join(KD_DIR if lib.startswith("KD_") else STOCK_FP, f"{lib}.pretty")
        for ref in refs.split():
            fp = pcbnew.FootprintLoad(path, name)
            if fp is None:
                raise SystemExit(f"{ref}: footprint {fpid} not found")
            fp.SetFPID(pcbnew.LIB_ID(lib, name))
            fp.SetReference(ref)
            fp.SetValue(VALUES.get(ref, val.split(" (")[0].split(",")[0]))
            x, y, rot = PLACEMENT[ref]
            fp.SetPosition(pt(x, y))
            fp.SetOrientationDegrees(rot)
            if ref in DNP:
                fp.SetDNP(True)
            board.Add(fp)
            pads = {pd.GetNumber() for pd in fp.Pads()}
            for pd in fp.Pads():
                n = netmap.get((ref, pd.GetNumber()))
                if n:
                    pd.SetNet(nets[n])
            missing_pads += [f"{r}.{p}" for (r, p) in netmap if r == ref and p not in pads]
            placed += 1
    if missing_pads:
        raise SystemExit(f"netlist pins without a pad: {missing_pads}")
    return placed


# ---------------------------------------------------------------------------
# Silkscreen for hand assembly (user 2026-11-27: stencil + reflow, parts placed with tweezers):
# * R / C: the VALUE on silk next to the part (reference moved to F.Fab for the assembly drawing);
#   other parts: the reference. Each label goes to the first free spot (no pad, hole, edge, other label or
#   foreign silk), 1.0 mm text, falling back to 0.8 mm.
# * pin-1 dot outside pad 1 of every part with 3+ pads; cathode bar outside pad 1 of every diode / LED.
# ---------------------------------------------------------------------------
def short_value(ref, val):
    v = val.split(" ")[0]
    if ref.startswith("C"):
        m = re.match(r"([\d.]+)([pnu])F", v)
        if m:
            num, unit = float(m.group(1)), m.group(2)
            if unit == "u" and num < 1:
                num, unit = num * 1000, "n"
            return f"{num:g}{unit}"
    return v


def _box(x0, y0, x1, y1):
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def _hit(a, b, m=0.0):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])


def _bb(item):
    b = item.GetBoundingBox()
    return _box(pcbnew.ToMM(b.GetX()), pcbnew.ToMM(b.GetY()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom()))


def silk_pass(board):
    ex0, ey0 = to_kicad(-BOARD_W / 2, -BOARD_H / 2)
    ex1, ey1 = to_kicad(BOARD_W / 2, BOARD_H / 2)
    pads, silk, marks1 = [], [], []                      # obstacles in sheet mm; marks1 = existing dots / arrows
    for fp in board.GetFootprints():
        for pd in fp.Pads():
            pads.append(_bb(pd))
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() != "PCB_TEXT":
                silk.append((fp.GetReference(), _bb(g)))
                if g.GetShape() in (pcbnew.SHAPE_T_CIRCLE, pcbnew.SHAPE_T_POLY):
                    marks1.append((fp.GetReference(), _bb(g)))
    labels, failed, marks, marked = [], [], 0, []

    def free(box, owner):
        if box[0] < ex0 + 0.5 or box[1] < ey0 + 0.5 or box[2] > ex1 - 0.5 or box[3] > ey1 - 0.5:
            return False
        if any(_hit(box, p, 0.2) for p in pads) or any(_hit(box, l, 0.25) for l in labels):
            return False
        return not any(o != owner and _hit(box, b, 0.15) for o, b in silk)

    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        if ref.startswith("H"):
            continue
        passive = re.match(r"[RC]\d", ref) is not None
        fref = fp.Reference()
        if passive:
            fref.SetLayer(pcbnew.F_Fab)
            fref.SetTextSize(pcbnew.VECTOR2I(MM(0.5), MM(0.5)))
            fref.SetTextThickness(MM(0.08))
            fref.SetPosition(fp.GetPosition())
            t = pcbnew.PCB_TEXT(board)
            t.SetText(short_value(ref, fp.GetValue()))
            t.SetLayer(pcbnew.F_SilkS)
            board.Add(t)
        else:
            t = fref
            t.SetVisible(True)
        t.SetTextAngleDegrees(0)
        t.SetKeepUpright(True)
        b = fp.GetBoundingBox(False, False)
        cx0, cy0, cx1, cy1 = (pcbnew.ToMM(b.GetX()), pcbnew.ToMM(b.GetY()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom()))
        mx, my = (cx0 + cx1) / 2, (cy0 + cy1) / 2
        ok = False
        for size in (1.0, 0.8):
            t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
            t.SetTextThickness(MM(0.15))
            t.SetTextAngleDegrees(0)
            t.SetPosition(pcbnew.VECTOR2I(0, 0))
            tb = _bb(t)
            w, h = tb[2] - tb[0], tb[3] - tb[1]
            vertical = round(fp.GetOrientationDegrees()) % 180 == 90
            cands = []
            for g in (0.35, 1.2):
                horiz = [(0, mx, cy0 - g - h / 2), (0, mx, cy1 + g + h / 2), (0, cx0 - g - w / 2, my),
                         (0, cx1 + g + w / 2, my), (0, cx0 - g - w / 2, cy0 - g - h / 2),
                         (0, cx1 + g + w / 2, cy0 - g - h / 2), (0, cx0 - g - w / 2, cy1 + g + h / 2),
                         (0, cx1 + g + w / 2, cy1 + g + h / 2)]
                rot = [(90, mx, cy0 - g - w / 2), (90, mx, cy1 + g + w / 2), (90, cx0 - g - h / 2, my),
                       (90, cx1 + g + h / 2, my)]
                cands += (rot + horiz) if vertical else (horiz + rot)
            for ang, x, y in cands:
                t.SetTextAngleDegrees(ang)
                t.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
                box = _bb(t)
                if free(box, ref):
                    labels.append(box)
                    ok = True
                    break
            if ok:
                break
        if not ok:
            failed.append(ref)
            t.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
            t.SetPosition(pcbnew.VECTOR2I(MM(mx), MM(cy0 - 0.9)))
        # polarity / pin-1 marks
        p1 = [pd for pd in fp.Pads() if pd.GetNumber() in ("1", "A1")]
        if not p1 or len(fp.Pads()) < 2 or ref.startswith(("BT", "J7", "J8")):
            continue
        pd = p1[0]
        pb = _bb(pd)
        px, py = (pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2
        fx, fy = pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y)
        dx, dy = px - fx, py - fy
        is_diode = ref.startswith("D")
        if is_diode:                                     # bar beyond the cathode pad, across the diode axis
            if abs(dx) >= abs(dy):
                xb = (pb[0] - 0.35) if dx < 0 else (pb[2] + 0.35)
                seg = ((xb, pb[1] - 0.2), (xb, pb[3] + 0.2))
            else:
                yb = (pb[1] - 0.35) if dy < 0 else (pb[3] + 0.35)
                seg = ((pb[0] - 0.2, yb), (pb[2] + 0.2, yb))
            own = [bx for o, bx in silk if o == ref]
            sb = _box(seg[0][0] - 0.125, seg[0][1] - 0.125, seg[1][0] + 0.125, seg[1][1] + 0.125)
            if any(_hit(sb, bx) for bx in own):          # the footprint already marks the cathode there: move out
                if abs(dx) >= abs(dy):
                    off = -0.4 if dx < 0 else 0.4
                    seg = ((seg[0][0] + off, seg[0][1]), (seg[1][0] + off, seg[1][1]))
                else:
                    off = -0.4 if dy < 0 else 0.4
                    seg = ((seg[0][0], seg[0][1] + off), (seg[1][0], seg[1][1] + off))
            sh = pcbnew.PCB_SHAPE(board)
            sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
            sh.SetStart(pcbnew.VECTOR2I(MM(seg[0][0]), MM(seg[0][1])))
            sh.SetEnd(pcbnew.VECTOR2I(MM(seg[1][0]), MM(seg[1][1])))
            sh.SetWidth(MM(0.25))
            sh.SetLayer(pcbnew.F_SilkS)
            board.Add(sh)
            marks += 1
            marked.append(ref)
            continue
        if len(fp.Pads()) < 3:
            continue
        n = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        ux, uy = dx / n, dy / n
        hw, hh = (pb[2] - pb[0]) / 2, (pb[3] - pb[1]) / 2
        placed = False
        for extra in (0.45, 0.7, 1.0):
            # outward from the part centre, past the pad edge
            k = min(hw / abs(ux) if abs(ux) > 1e-6 else 1e9, hh / abs(uy) if abs(uy) > 1e-6 else 1e9)
            cx, cy = px + ux * (k + extra), py + uy * (k + extra)
            dot = _box(cx - 0.3, cy - 0.3, cx + 0.3, cy + 0.3)
            if any(_hit(dot, bx, 0.3) for o, bx in marks1 if o == ref):
                placed = True                            # footprint already has a pin-1 mark there
                break
            if not any(_hit(dot, p, 0.15) for p in pads) and not any(_hit(dot, l, 0.1) for l in labels):
                c = pcbnew.PCB_SHAPE(board)
                c.SetShape(pcbnew.SHAPE_T_CIRCLE)
                c.SetCenter(pcbnew.VECTOR2I(MM(cx), MM(cy)))
                c.SetEnd(pcbnew.VECTOR2I(MM(cx + 0.15), MM(cy)))
                c.SetWidth(MM(0.3))
                c.SetFilled(True)
                c.SetLayer(pcbnew.F_SilkS)
                board.Add(c)
                marks += 1
                marked.append(ref)
                placed = True
                break
        if not placed:
            failed.append(ref + " pin1")
    print("  marks added:", " ".join(marked))
    return len(labels), marks, failed


def main():
    write_hole_fp()
    board = pcbnew.BOARD()
    board.GetDesignSettings().SetBoardThickness(MM(1.6))
    tb = board.GetTitleBlock()
    tb.SetTitle(PROJECT)
    tb.SetRevision(REVISION)
    tb.SetDate(DATE)
    tb.SetComment(0, "Stage 3: placement (KiCad-Designs/PicoBalancer)")
    w, h = BOARD_W / 2, BOARD_H / 2
    rect(board, -w, -h, w, h, pcbnew.Edge_Cuts, 0.1)
    for i, (x, y) in enumerate(HOLES):
        hole(board, f"H{i + 1}", x, y)
        k = HOLE_KEEPOUT / 2
        rect(board, x - k, y - k, x + k, y + k, pcbnew.Cmts_User)
        c = pcbnew.PCB_SHAPE(board)                   # M2.5 head keep-out: housing >= 7.5 mm from the hole centre
        c.SetShape(pcbnew.SHAPE_T_CIRCLE)
        c.SetCenter(pt(x, y))
        c.SetEnd(pt(x + BOLT_KEEPOUT_R, y))
        c.SetLayer(pcbnew.Dwgs_User)
        c.SetWidth(MM(0.1))
        board.Add(c)
    cx, cy = HOLDER_CHANNEL["x"], HOLDER_CHANNEL["y"]
    rect(board, cx[0], cy[0], cx[1], cy[1], pcbnew.Dwgs_User, 0.05)
    for i, (x, y, d) in enumerate(CLAMP_HOLES):           # battery-clamp bolts (Fusion PCB body, user)
        hole(board, f"H{len(HOLES) + i + 1}", x, y)
    px0, py0, px1, py1 = COVER_PILLAR
    rect(board, px0, py0, px1, py1, pcbnew.Dwgs_User, 0.1)
    text(board, "cover pillar", 0, -71, pcbnew.Dwgs_User, 0.9)
    (ex0, ex1), (ey0, ey1) = ENCODER_ZONE
    for sx in (-1, 1):
        rect(board, sx * ex0, ey0, sx * ex1, ey1, pcbnew.Dwgs_User, 0.05)
    text(board, "encoder connectors (on motors)", 0, 108, pcbnew.Dwgs_User, 1.2)
    t_title = text(board, f"{PROJECT} V01", 0, 21.0, pcbnew.F_SilkS, 3.0)        # board name (user: enlarged)
    n_parts = place_parts(board)
    n_lab, n_marks, silk_failed = silk_pass(board)
    print(f"silk: {n_lab} labels, {n_marks} polarity / pin-1 marks; not placed cleanly: {silk_failed or 'none'}")
    board.Save(PCB)
    def table(name, libs, ext):
        rows = [f'  (lib (name "{n}")(type "KiCad")(uri "${{KIPRJMOD}}/../Libraries/{n}{ext}")(options "")(descr ""))'
                for n in libs]
        with open(os.path.join(ROOT, name), "w") as f:
            f.write("\n".join([f"({name.replace('-', '_')}", "  (version 7)"] + rows + [")"]) + "\n")
    table("fp-lib-table", ("KD_Mechanical", "KD_Power", "KD_Sensors", "KD_Modules", "KD_Connectors", "KD_Switches"), ".pretty")
    table("sym-lib-table", ("KD_Power", "KD_Sensors", "KD_Modules"), ".kicad_sym")
    if not os.path.exists(PRO):
        json.dump({"meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1}, "board": {}, "sheets": [],
                   "boards": [], "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []}},
                  open(PRO, "w"), indent=2)
    # check: every board hole matches a DXF circle (0.01 mm, same diameter), and the counts agree
    dx = dxf_circles()
    bad = [h_ for h_ in HOLES if not any(abs(h_[0] - x) < 0.01 and abs(h_[1] - y) < 0.01 and abs(d - HOLE_D) < 0.01
                                          for x, y, d in dx)]
    print(f"{n_parts} parts placed; {len(HOLES)} holes, {len(dx)} DXF circles, outline {BOARD_W} x {BOARD_H}: "
          + ("IMPORT OK" if not bad and len(dx) == len(HOLES) else f"IMPORT FAIL {bad}"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
