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
                    BOM, DNP, PLACEMENT, VALUES, build_nets, ANTENNA_KEEPOUT)

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
# Block titles on the silkscreen: (text, centre x, y in board mm, text size mm, bold[, angle]), placed before the part labels.
BLOCK_TITLES = [
    # each title above its area (user)
    ("USB CHARGE", (0.0, -97.6), 1.5, True),          # above the USB-C port
    ("CHARGER", (0.0, -54.8), 1.2, False),            # just below the cover pillar, above U6
    ("CELL PROTECTION", (0.0, -8.0), 1.0, False),     # in the channel above the two fuse / FET groups
    ("BOOST 5V1", (-22.0, 45.5), 1.2, False),
    ("MOTOR L", (-20.5, 68.3), 1.2, False),
    ("MOTOR R", (20.5, 68.3), 1.2, False),
    ("IMU", (-3.2, 84.6), 1.2, False),
    ("POWER", (20.25, 19.6), 1.2, False),
    # SW1 direction (NKK Series AS: actuator at the terminal-1 end = LEFT position = 2-1 connected; pin 1 -> BAT = ON):
    # slide toward pin 1 (up, toward the cells) = ON, toward pin 3 (down) = OFF
    ("ON", (20.25, 21.8), 1.2, True),
    ("OFF", (20.25, 34.9), 1.2, True),
    ("Pico W / Pico 2 W", (0.0, 48.0), 2.0, True, 90),
    ("BOOT", (5.5, 98.35), 0.8, False),                 # under TP1 (BNO086 BOOTN)
    ("GND", (8.6, 98.35), 0.8, False),                  # under TP2   # under the module, between the socket rows (user)
]
SILK_LABELS = {"TP1": "", "TP2": ""}     # test pads: fixed BOOT / GND titles under them    # custom silk labels (user: mark TP2 as GND)


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

    # board-level silk text (title) is an obstacle too
    for d in board.Drawings():
        if d.GetLayer() == pcbnew.F_SilkS and d.GetClass() == "PCB_TEXT":
            labels.append(_bb(d))
    # block titles first, at fixed positions (user: name each block; "USB CHARGE" in bold above the port); part labels
    # then find free spots around them
    for title, (x, y), size, bold, *ang in BLOCK_TITLES:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(title)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
        t.SetTextThickness(MM(max(0.15, size * 0.15)))
        t.SetBold(bold)
        t.SetTextAngleDegrees(ang[0] if ang else 0)
        t.SetPosition(pt(x, y))
        board.Add(t)
        box = _bb(t)
        if not free(box, None):
            failed.append("title " + title)
        labels.append(box)

    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        if ref.startswith("H"):
            continue
        passive = re.match(r"[RC]\d", ref) is not None or ref in SILK_LABELS
        fref = fp.Reference()
        if ref in SILK_LABELS and not SILK_LABELS[ref]:   # labelled by a fixed title instead (BLOCK_TITLES)
            fref.SetLayer(pcbnew.F_Fab)
            fref.SetTextSize(pcbnew.VECTOR2I(MM(0.5), MM(0.5)))
            fref.SetTextThickness(MM(0.08))
            fref.SetPosition(fp.GetPosition())
            continue
        if passive:
            fref.SetLayer(pcbnew.F_Fab)
            fref.SetTextSize(pcbnew.VECTOR2I(MM(0.5), MM(0.5)))
            fref.SetTextThickness(MM(0.08))
            fref.SetPosition(fp.GetPosition())
            t = pcbnew.PCB_TEXT(board)
            t.SetText(SILK_LABELS.get(ref) or short_value(ref, fp.GetValue()))
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


def antenna_keepout(board):
    """Rule area under the Pico W antenna on both copper layers: no tracks, vias, pads or pour."""
    x0, y0, x1, y1 = ANTENNA_KEEPOUT
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        (z.SetDoNotAllowZoneFills if hasattr(z, "SetDoNotAllowZoneFills") else z.SetDoNotAllowCopperPour)(True)
        z.SetDoNotAllowPads(True)
        z.SetDoNotAllowFootprints(False)
        z.SetLayer(layer)
        z.SetZoneName("Pico W antenna keep-out")
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(pt(x, y))
        board.Add(z)
    rect(board, x0, y0, x1, y1, pcbnew.Cmts_User, 0.1)
    text(board, "ANTENNA KEEP-OUT", (x0 + x1) / 2, (y0 + y1) / 2, pcbnew.Cmts_User, 1.0)


def add_routes(board):
    """Tracks and vias from routes.py (hand routing, board coordinates)."""
    import importlib
    import routes
    importlib.reload(routes)
    lay = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
    missing = set()
    for net, layer, w, pts in routes.TRACKS:
        ni = board.FindNet(net)
        if ni is None:
            missing.add(net)
            continue
        for a, b in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pt(*a))
            t.SetEnd(pt(*b))
            t.SetWidth(MM(w))
            t.SetLayer(lay[layer])
            t.SetNet(ni)
            board.Add(t)
    for net, x, y, d, drill in routes.VIAS:
        ni = board.FindNet(net)
        if ni is None:
            missing.add(net)
            continue
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pt(x, y))
        v.SetWidth(MM(d))
        v.SetDrill(MM(drill))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(ni)
        board.Add(v)
    if missing:
        raise SystemExit(f"routes.py: unknown nets {sorted(missing)}")
    return len(routes.TRACKS), len(routes.VIAS)


POWER_NETS = {"BAT", "VBUS", "SYS", "PMID", "5V1", "VSW", "VSYS", "CELL1", "CELL2", "CELL1_F", "CELL2_F", "CHG_SW",
              "BOOST_SW", "M1_OUT1", "M1_OUT2", "M2_OUT1", "M2_OUT2", "GND"}
BUILD = os.path.join(ROOT, "build")


def _bbox(item):
    b = item.GetBoundingBox()
    return [pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom())]


def export_geom(board):
    """build/geometry.json for router.py: outline, pads, keep-outs, existing (hand-routed) tracks and vias, nets."""
    cu = {pcbnew.F_Cu: "F", pcbnew.B_Cu: "B"}
    pads = []
    for fp in board.GetFootprints():
        for pd in fp.Pads():
            pads.append({"ref": fp.GetReference(), "pin": pd.GetNumber(), "net": pd.GetNetname(),
                         "layers": [n for l, n in cu.items() if pd.IsOnLayer(l)], "bbox": _bbox(pd)})
    keepouts = []
    for z in board.Zones():
        if z.GetIsRuleArea():
            ol = z.Outline().Outline(0)
            keepouts.append({"layers": [n for l, n in cu.items() if z.IsOnLayer(l)],
                             "pts": [(pcbnew.ToMM(ol.CPoint(i).x), pcbnew.ToMM(ol.CPoint(i).y))
                                     for i in range(ol.PointCount())]})
    tracks, vias = [], []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            vias.append({"net": t.GetNetname(), "x": pcbnew.ToMM(p.x), "y": pcbnew.ToMM(p.y), "d": pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))})
        else:
            a, b = t.GetStart(), t.GetEnd()
            tracks.append({"net": t.GetNetname(), "layer": cu[t.GetLayer()], "x1": pcbnew.ToMM(a.x), "y1": pcbnew.ToMM(a.y),
                           "x2": pcbnew.ToMM(b.x), "y2": pcbnew.ToMM(b.y), "w": pcbnew.ToMM(t.GetWidth())})
    x0, y0 = to_kicad(-BOARD_W / 2, -BOARD_H / 2)
    x1, y1 = to_kicad(BOARD_W / 2, BOARD_H / 2)
    nets = {n: {"pins": c, "power": n in POWER_NETS} for n, c in build_nets().items()}
    os.makedirs(BUILD, exist_ok=True)
    json.dump({"outline": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "pads": pads, "shapes": [], "keepouts": keepouts,
               "tracks": tracks, "vias": vias, "nets": nets}, open(os.path.join(BUILD, "geometry.json"), "w"))
    print(f"geometry: {len(pads)} pads, {len(tracks)} tracks, {len(vias)} vias, {len(keepouts)} keep-outs")


def import_routes(board):
    data = json.load(open(os.path.join(BUILD, "routes.json")))
    lay = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
    for t in data["tracks"]:
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(pcbnew.VECTOR2I(MM(t["x1"]), MM(t["y1"])))
        tr.SetEnd(pcbnew.VECTOR2I(MM(t["x2"]), MM(t["y2"])))
        tr.SetWidth(MM(t["w"]))
        tr.SetLayer(lay[t["layer"]])
        tr.SetNet(board.FindNet(t["net"]))
        board.Add(tr)
    for v in data["vias"]:
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I(MM(v["x"]), MM(v["y"])))
        via.SetWidth(MM(v["d"]))
        via.SetDrill(MM(v["drill"]))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(board.FindNet(v["net"]))
        board.Add(via)
    # the router works on pad bounding boxes: a track end inside a round pad's box but outside its copper is
    # extended to the pad centre (same layer, same net)
    lay_of = {pcbnew.F_Cu: "F", pcbnew.B_Cu: "B"}
    pads = [(pd, _bbox(pd)) for fp in board.GetFootprints() for pd in fp.Pads() if pd.GetNetname()]
    fixed = 0
    for t in data["tracks"]:
        for x, y in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
            for pd, (x0, y0, x1, y1) in pads:
                if pd.GetNetname() != t["net"] or not (x0 <= x <= x1 and y0 <= y <= y1):
                    continue
                if not pd.IsOnLayer(lay[t["layer"]]):
                    continue
                if pd.HitTest(pcbnew.VECTOR2I(MM(x), MM(y))):
                    break
                c = pd.GetPosition()
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(MM(x), MM(y)))
                tr.SetEnd(c)
                tr.SetWidth(MM(min(t["w"], 0.25)))
                tr.SetLayer(lay[t["layer"]])
                tr.SetNet(board.FindNet(t["net"]))
                board.Add(tr)
                fixed += 1
                break
    print(f"router: {len(data['tracks'])} segments, {len(data['vias'])} vias; failed {data['failed']}; "
          f"{fixed} ends extended to pad centres")


def gnd_pours(board):
    """GND pour on both copper layers over the whole board (0.25 mm clearance, thermal reliefs on pads)."""
    x0, y0 = to_kicad(-BOARD_W / 2, -BOARD_H / 2)
    x1, y1 = to_kicad(BOARD_W / 2, BOARD_H / 2)
    gnd = board.FindNet("GND")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetLocalClearance(MM(0.25))
        z.SetMinThickness(MM(0.25))
        z.SetThermalReliefGap(MM(0.3))
        z.SetThermalReliefSpokeWidth(MM(0.4))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(pcbnew.VECTOR2I(MM(x), MM(y)))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


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
    t_title = text(board, f"{PROJECT} V01", 0, 16.5, pcbnew.F_SilkS, 3.0)        # board name (user: enlarged)
    t_title.SetBold(True)                                                          # user: bold
    n_parts = place_parts(board)
    antenna_keepout(board)
    n_tr, n_via = add_routes(board)
    print(f"routes: {n_tr} tracks, {n_via} vias")
    n_lab, n_marks, silk_failed = silk_pass(board)
    print(f"silk: {n_lab} labels, {n_marks} polarity / pin-1 marks; not placed cleanly: {silk_failed or 'none'}")
    if "geom" in sys.argv:
        export_geom(board)
    if "finish" in sys.argv:
        import_routes(board)
        gnd_pours(board)
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
