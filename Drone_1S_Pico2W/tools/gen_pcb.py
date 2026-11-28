#!/usr/bin/python3
"""
Generate the bare boards (run with the system interpreter, which has pcbnew):

    /usr/bin/python3 gen_pcb.py            # both boards
    /usr/bin/python3 gen_pcb.py frame|fc
    gen_pcb.py fc geom                     # FC with nets + hand routes (routes_fc.py) -> build/fc_geometry.json
    gen_pcb.py fc finish                   # ... + router output build/fc_routes.json + GND pours, then DRC
(Windows: "C:/Program Files/KiCad/10.0/bin/python.exe")

Each board gets: .kicad_pro (rules), .kicad_pcb (outline, holes, fixed pads,
placement guides on Dwgs.User = top side / Cmts.User = bottom side), and a DRC
report in ../build/<board>_drc.txt.
"""

import json
import math
import os
import subprocess
import sys

import pcbnew

import dxf_import
from gen_libs import gen_lib                      # shared library generator (Libraries/tools)
PICO_TP, PICO_SWD = gen_lib.PICO_TP, gen_lib.PICO_SWD
from design import (FC, FRAME, SHARED_LIBS, DECK_LEFT, DECK_RIGHT, B2B, B2B_PIN_X, FRAME_CONN, MOTORS, MOTOR_NAMES, SCAD, ESC_PAD, TAB_PAD_SIZE, TAB_PAD_X,
                    REVISION, DATE, to_kicad, uid, ORIGIN_X, ORIGIN_Y)
import fc_design

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
BUILD = os.path.join(ROOT, "build")
KFP = next(p for p in ("C:/Program Files/KiCad/10.0/share/kicad/footprints", "/usr/share/kicad/footprints")
           if os.path.isdir(p))

KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
mm = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def VS(x, y):
    """scad (x forward, y left) -> KiCad board coordinates."""
    return V(*to_kicad(x, y))


# ---------------------------------------------------------------------------
# project file (rules = AGENTS.md section 6, strictest fab)
# ---------------------------------------------------------------------------
def write_project(path, power_patterns=()):
    nc = lambda name, w, vd, vdr: {
        "name": name, "clearance": 0.2, "track_width": w, "via_diameter": vd, "via_drill": vdr,
        "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_gap": 0.25,
        "diff_pair_width": 0.2, "diff_pair_via_gap": 0.25, "bus_width": 12, "wire_width": 6,
        "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
        "schematic_color": "rgba(0, 0, 0, 0.000)"}
    pro = {
        "board": {"design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2,
                         "copper_text_size_h": 1.5, "copper_text_size_v": 1.5,
                         "copper_text_thickness": 0.3, "silk_line_width": 0.15,
                         "silk_text_size_h": 1.0, "silk_text_size_v": 1.0,
                         "silk_text_thickness": 0.15},
            "rules": {"min_clearance": 0.15, "min_track_width": 0.15,
                      "min_via_annular_width": 0.1, "min_via_diameter": 0.5,
                      "min_through_hole_diameter": 0.3, "min_hole_to_hole": 0.25,
                      "min_hole_clearance": 0.25, "min_copper_edge_clearance": 0.4,
                      "min_silk_clearance": 0.0, "min_text_height": 0.6,
                      "min_text_thickness": 0.1, "solder_mask_to_copper_clearance": 0.0},
            "track_widths": [0.0, 0.25, 0.4, 0.5, 1.0, 2.0],
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0},
                               {"diameter": 0.6, "drill": 0.3},
                               {"diameter": 0.8, "drill": 0.4}],
            "rule_severities": {"silk_overlap": "ignore", "silk_over_copper": "warning",
                                "lib_footprint_issues": "ignore",
                                "lib_footprint_mismatch": "ignore",
                                # FC SW1 (B3U-1000PM-B) boss hole sits under the Pico's courtyard: an unplated
                                # 0.8 mm hole under the module's bare underside, ~6 mm from TP1 - reported as a
                                # warning (listed by finish()), not an error.
                                "npth_inside_courtyard": "warning"},
        }},
        "meta": {"filename": os.path.basename(path), "version": 1},
        "net_settings": {
            "classes": [nc("Default", 0.25, 0.6, 0.3), nc("Power", 0.5, 0.8, 0.4)],
            "meta": {"version": 3}, "net_colors": None, "netclass_assignments": None,
            "netclass_patterns": [{"netclass": "Power", "pattern": p} for p in power_patterns],
        },
        "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [[uid(os.path.basename(path) + "-root"), ""]],
        "text_variables": {},
    }
    with open(path, "w") as f:
        json.dump(pro, f, indent=2)


# ---------------------------------------------------------------------------
# drawing helpers
# ---------------------------------------------------------------------------
def shape(board, kind, layer, w=0.1, fill=False):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(kind)
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    if fill:
        s.SetFilled(True)
    board.Add(s)
    return s


def seg(board, a, b, layer=pcbnew.Edge_Cuts, w=0.1):
    s = shape(board, pcbnew.SHAPE_T_SEGMENT, layer, w)
    s.SetStart(a)
    s.SetEnd(b)


def arc(board, a, m, b, layer=pcbnew.Edge_Cuts, w=0.1):
    s = shape(board, pcbnew.SHAPE_T_ARC, layer, w)
    s.SetArcGeometry(a, m, b)


def circle(board, c, r, layer, w=0.1):
    s = shape(board, pcbnew.SHAPE_T_CIRCLE, layer, w)
    s.SetCenter(c)
    s.SetEnd(pcbnew.VECTOR2I(c.x + mm(r), c.y))


def poly(board, pts, layer, w=0.1):
    for i in range(len(pts)):
        seg(board, pts[i - 1], pts[i], layer, w)


def rect_s(cx, cy, l, w, ang=0.0):
    """Rectangle corners in scad coordinates (centre, length along ang, width)."""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [VS(cx + c * u - s * v, cy + s * u + c * v)
            for u, v in ((-l / 2, -w / 2), (l / 2, -w / 2), (l / 2, w / 2), (-l / 2, w / 2))]


def text(board, txt, p, layer, size=1.0, thick=0.15, rot=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(p)
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(thick))
    if rot:
        t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    if layer in (pcbnew.B_SilkS, pcbnew.B_Cu, pcbnew.B_Fab):
        t.SetMirrored(True)
    board.Add(t)


def load_fp(lib, name):
    """Stock KiCad library, or a shared KD_* library (KiCad-Designs/Libraries)."""
    base = os.path.join(ROOT, SHARED_LIBS) if lib.startswith("KD_") else KFP
    fp = pcbnew.FootprintLoad(os.path.join(base, f"{lib}.pretty"), name)
    if fp is None:
        raise RuntimeError(f"footprint {lib}:{name} not found" + (" - run Libraries/tools/gen_lib.py" if lib.startswith("KD_") else ""))
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def rule_area(board, pts, layer, name):
    """Keep-out: no tracks, vias, pads or pours on `layer`."""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetLayer(layer)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowFootprints(False)
    z.SetZoneName(name)
    o = z.Outline()
    o.NewOutline()
    for p in pts:
        o.Append(p.x, p.y)
    board.Add(z)


def place_b2b(board, lib, name, ref, value, row_sign, bottom, row_y=None):
    """Place a 1x10 board-to-board part so that pad k sits at scad
    (B2B_PIN_X[k-1], row_sign * row_y), on the given side. Tries the four
    orientations and keeps the one that matches (asserted)."""
    y = row_sign * (B2B["row_y"] if row_y is None else row_y)
    want = {str(k + 1): VS(B2B_PIN_X[k], y) for k in range(B2B["pins"])}
    fp = load_fp(lib, name)
    fp.SetReference(ref)
    fp.SetValue(value)
    board.Add(fp)                       # KiCad 7: Flip() needs the parent board
    if bottom:
        fp.Flip(fp.GetPosition(), True)
    tgt = VS(0.5 * (B2B_PIN_X[0] + B2B_PIN_X[-1]), y)
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        pads = {p.GetNumber(): p.GetPosition() for p in fp.Pads()}
        mid = pcbnew.VECTOR2I((pads["1"].x + pads["10"].x) // 2, (pads["1"].y + pads["10"].y) // 2)
        fp.Move(pcbnew.VECTOR2I(tgt.x - mid.x, tgt.y - mid.y))
        got = {p.GetNumber(): p.GetPosition() for p in fp.Pads()}
        # SMD sockets alternate pads either side of the pin line: check along the row exactly
        if all(abs(got[k].x - want[k].x) < mm(0.01) for k in want) and \
           all(abs(got[k].y - want[k].y) < mm(2.0) for k in want):
            assert all(p.IsOnLayer(pcbnew.B_Cu if bottom else pcbnew.F_Cu) for p in fp.Pads())
            return fp
    raise AssertionError(f"{ref}: no orientation puts pin k at x = 9 - 2(k-1)")


def poly_set(pts_mm):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in pts_mm:
        kx, ky = to_kicad(x, y)
        s.Append(mm(kx), mm(ky))
    return s


def capsule(p, q, r, n=24):
    """Stadium between scad points p and q, radius r, as a point list."""
    a = math.atan2(q[1] - p[1], q[0] - p[0])
    pts = [(q[0] + r * math.cos(a - math.pi / 2 + math.pi * i / n), q[1] + r * math.sin(a - math.pi / 2 + math.pi * i / n)) for i in range(n + 1)]
    pts += [(p[0] + r * math.cos(a + math.pi / 2 + math.pi * i / n), p[1] + r * math.sin(a + math.pi / 2 + math.pi * i / n)) for i in range(n + 1)]
    return pts


# KiCad 7 needs a POLYGON_MODE argument on the polygon booleans; KiCad 8+ dropped it.
_PM = (pcbnew.SHAPE_POLY_SET.PM_STRICTLY_SIMPLE,) if hasattr(pcbnew.SHAPE_POLY_SET, "PM_STRICTLY_SIMPLE") else ()


def fc_outline_pts():
    """Minimum FC outline (scad points, closed polygon), see design.FC."""
    x0, x1, by = FC["band"]
    mx, my = FC["middle"]
    shape = poly_set([(x0, -by), (x1, -by), (x1, by), (x0, by)])
    shape.BooleanAdd(poly_set([(-mx, -my), (mx, -my), (mx, my), (-mx, my)]), *_PM)
    rx, ry = FC["ear_root"]
    for hx, hy in FC["holes"]:
        root = (math.copysign(rx, hx), math.copysign(ry, hy))
        shape.BooleanAdd(poly_set(capsule((hx, hy), root, FC["ear_r"])), *_PM)
    nw, nd = FC["notch"]
    pico_end = FC["pico_c"][0] + FC["pico_size"][0] / 2
    shape.BooleanSubtract(poly_set([(pico_end - nd, -nw / 2), (pico_end + 10, -nw / 2), (pico_end + 10, nw / 2), (pico_end - nd, nw / 2)]), *_PM)
    shape = shape.Fillet(mm(FC["fillet"]), mm(0.01))
    assert shape.OutlineCount() == 1 and shape.HoleCount(0) == 0
    o = shape.Outline(0)
    pts = []
    for i in range(o.PointCount()):
        v = o.CPoint(i)
        pts.append((pcbnew.ToMM(v.x) - ORIGIN_X, ORIGIN_Y - pcbnew.ToMM(v.y)))
    return pts


def new_fp(board, ref, value, pos, name):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetFPID(pcbnew.LIB_ID("Drone_1S_Board", name))   # drawn by this script, no library
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(pos)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    for f in (fp.Reference(), fp.Value()):
        f.SetLayer(pcbnew.F_Fab)
    board.Add(fp)
    return fp


# KiCad 7 footprint items keep a footprint-relative copy (SetLocalCoord, FP_SHAPE); KiCad 8+ derive it.
_FP_SHAPE = getattr(pcbnew, "FP_SHAPE", pcbnew.PCB_SHAPE)


def _local(item):
    if hasattr(item, "SetLocalCoord"):
        item.SetLocalCoord()


def add_pad(fp, num, pos, kind, size, drill=0.0, layers=None, shape_=pcbnew.PAD_SHAPE_CIRCLE):
    p = pcbnew.PAD(fp)
    p.SetNumber(str(num))
    p.SetAttribute(kind)
    p.SetShape(shape_)
    p.SetSize(pcbnew.VECTOR2I(mm(size[0]), mm(size[1])))
    if drill:
        p.SetDrillSize(pcbnew.VECTOR2I(mm(drill), mm(drill)))
    if layers is None:
        layers = {pcbnew.PAD_ATTRIB_PTH: p.PTHMask(), pcbnew.PAD_ATTRIB_NPTH: p.UnplatedHoleMask(),
                  pcbnew.PAD_ATTRIB_SMD: p.SMDMask()}[kind]
    p.SetLayerSet(layers)
    fp.Add(p)
    p.SetPosition(pos)
    _local(p)                  # KiCad 7: store pos0 (footprint-relative) from the absolute position
    return p


def fp_circle(fp, c, r, layer, w=0.05):
    s = _FP_SHAPE(fp, pcbnew.SHAPE_T_CIRCLE)
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    fp.Add(s)
    s.SetCenter(c)
    s.SetEnd(pcbnew.VECTOR2I(c.x + mm(r), c.y))
    _local(s)


def fp_poly(fp, pts, layer, w=0.05):
    for i in range(len(pts)):
        s = _FP_SHAPE(fp, pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(layer)
        s.SetWidth(mm(w))
        fp.Add(s)
        s.SetStart(pts[i - 1])
        s.SetEnd(pts[i])
        _local(s)


def new_board(path, title, thickness, comment):
    if os.path.exists(path):
        os.remove(path)
    board = pcbnew.NewBoard(path)
    board.SetCopperLayerCount(2)
    tb = board.GetTitleBlock()
    tb.SetTitle(title)
    tb.SetRevision(REVISION)
    tb.SetDate(DATE)
    tb.SetCompany("KiCad-Designs")
    tb.SetComment(0, comment)
    tb.SetComment(1, f"{thickness:.1f} mm FR4, 2 layers - stage 1: bare board")
    board.GetDesignSettings().SetBoardThickness(mm(thickness))
    return board


def isolated_gnd_vias(board):
    """GND vias whose pour islands (followed through other GND vias) reach no GND pad: stitching that landed in pockets
    cut off by tracks. Returns their positions (KiCad mm) for removal."""
    cu = (pcbnew.F_Cu, pcbnew.B_Cu)
    islands = []                                      # (layer, SHAPE_POLY_SET)
    for z in board.Zones():
        if z.GetNetname() != "GND":
            continue
        for L in cu:
            if not z.IsOnLayer(L):
                continue
            fp = z.GetFilledPolysList(L)
            for i in range(fp.OutlineCount()):
                s = pcbnew.SHAPE_POLY_SET()
                s.AddOutline(fp.Outline(i))
                for h in range(fp.HoleCount(i)):
                    s.AddHole(fp.Hole(i, h))
                islands.append((L, s))
    anchor = [False] * len(islands)
    for fp in board.GetFootprints():
        for pd in fp.Pads():
            if pd.GetNetname() != "GND":
                continue
            r = max(pd.GetSize().x, pd.GetSize().y) // 2 + mm(0.6)
            for k, (L, s) in enumerate(islands):
                if pd.IsOnLayer(L) and s.Contains(pd.GetPosition(), -1, r):
                    anchor[k] = True
    vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND"]
    vis = [[k for k, (L, s) in enumerate(islands) if s.Contains(v.GetPosition(), -1, mm(0.35))] for v in vias]
    parent = list(range(len(islands)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for ks in vis:
        for a, b in zip(ks, ks[1:]):
            parent[find(a)] = find(b)
    good = {find(k) for k in range(len(islands)) if anchor[k]}
    out = []
    for v, ks in zip(vias, vis):
        if not ks or all(find(k) not in good for k in ks):
            p_ = v.GetPosition()
            out.append((pcbnew.ToMM(p_.x), pcbnew.ToMM(p_.y)))
    return out


def finish(board, path, name):
    os.makedirs(BUILD, exist_ok=True)
    pcbnew.SaveBoard(path, board)
    board = pcbnew.LoadBoard(path)
    rpt = os.path.join(BUILD, f"{name}_drc.txt")
    if os.path.isfile(KICAD_CLI):      # KiCad 8+: WriteDRCReport() needs the GUI, so use kicad-cli
        refill = ["--refill-zones", "--save-board"] if list(board.Zones()) else []   # pours filled by KiCad itself
        subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "report", "--units", "mm", *refill, "-o", rpt, path],
                       check=True, capture_output=True)
    else:                              # KiCad 7 in the container
        pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(rpt).read()
    import re
    dang = [(float(x), float(y)) for x, y in re.findall(
        r"\[via_dangling\][^\n]*\n[^\n]*\n\s+@\(([-\d.]+) mm, ([-\d.]+) mm\): Via \[GND\]", txt)]   # stitching only:
    # a one-sided signal via can still be the joint between a hand escape and a router track on the same layer
    dang += [(float(x), float(y)) for x, y in re.findall(
        r"\[unconnected_items\][^\n]*\n[^\n]*\n(?:\s+@[^\n]*\n)?\s+@\(([-\d.]+) mm, ([-\d.]+) mm\): Via \[GND\]", txt)]
    if list(board.Zones()):
        dang += isolated_gnd_vias(board)
    if dang and os.path.isfile(KICAD_CLI) and list(board.Zones()):
        # vias left on one layer (an escape the router finished on the other side, or a stitching via that landed in
        # an enclosed pour pocket) are removed, then the pours are refilled and DRC runs again
        n = 0
        for t in list(board.GetTracks()):
            if t.GetClass() == "PCB_VIA":
                p_ = t.GetPosition()
                if any(abs(pcbnew.ToMM(p_.x) - x) < 0.01 and abs(pcbnew.ToMM(p_.y) - y) < 0.01 for x, y in dang):
                    board.Remove(t)
                    n += 1
        pcbnew.SaveBoard(path, board)
        subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "report", "--units", "mm", "--refill-zones",
                        "--save-board", "-o", rpt, path], check=True, capture_output=True)
        board = pcbnew.LoadBoard(path)
        txt = open(rpt).read()
        print(f"  removed {n} dangling vias, DRC re-run")
    counts = {k: int(v) for v, k in re.findall(r"\*\* Found (\d+) (DRC violations|unconnected pads|Footprint errors)", txt)}
    warns = re.findall(r"^\[(\w+)\]: (.*)\n\s+[^\n]*; warning", txt, re.M)
    if warns:                          # warnings are listed, and only errors count against the gate
        counts["DRC violations"] -= len(warns)
        for rule, msg in warns:
            print(f"  DRC warning (accepted): {rule}: {msg}")
    bb = board.GetBoardEdgesBoundingBox()
    print(f"{name}: {len(board.GetFootprints())} footprints, "
          f"{sum(len(f.Pads()) for f in board.GetFootprints())} pads, "
          f"edge bbox {pcbnew.ToMM(bb.GetWidth()):.2f} x {pcbnew.ToMM(bb.GetHeight()):.2f} mm, "
          f"thickness {pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness()):.1f} mm, DRC {counts}")
    return counts


# ---------------------------------------------------------------------------
# Frame
# ---------------------------------------------------------------------------
def nearest_motor(x, y):
    return min(range(4), key=lambda i: math.hypot(MOTORS[i][0] - x, MOTORS[i][1] - y))


def build_frame():
    d = os.path.join(ROOT, "Frame")
    os.makedirs(d, exist_ok=True)
    name = FRAME["project"]
    pcb = os.path.join(d, f"{name}.kicad_pcb")
    write_project(os.path.join(d, f"{name}.kicad_pro"), ("BAT*", "VBAT*", "ESC*_V*", "VSYS", "SYS", "5V1"))
    board = new_board(pcb, FRAME["title"], FRAME["thickness"],
                      "Outline + holes imported from OpenScad-Designs/Drones/1S_PiZero (pcb_outline DXF)")

    outline, holes = dxf_import.load()
    poly(board, [VS(x, y) for x, y in outline], pcbnew.Edge_Cuts, 0.1)

    # --- motor mounts: shaft clearance + 4 x M2, one footprint per motor ---
    for i, (mx, my) in enumerate(MOTORS):
        fp = new_fp(board, f"H{i + 1}", f"Motor 1203 {MOTOR_NAMES[i]}", VS(mx, my), "MotorMount_1203_M2_9mm")
        own = [h for h in holes if h["kind"] in ("motor_shaft", "m2")
               and math.hypot(h["x"] - mx, h["y"] - my) < 6]
        assert len(own) == 5, own
        for h in own:
            add_pad(fp, "", VS(h["x"], h["y"]), pcbnew.PAD_ATTRIB_NPTH, (h["d"], h["d"]), h["d"])
        fp_circle(fp, VS(mx, my), SCAD["motor_bell_d"] / 2, pcbnew.F_Fab, 0.1)
        fp_circle(fp, VS(mx, my), 6.5, pcbnew.F_CrtYd)

    # --- ESC header pads: inner row 1..4, outer row 5..7 (scad esc_pins order) ---
    pins = [h for h in holes if h["kind"] == "esc_pin"]
    for i, (mx, my) in enumerate(MOTORS):
        u = (mx / math.hypot(mx, my), my / math.hypot(mx, my))
        p = (-u[1], u[0])
        own = [h for h in pins if nearest_motor(h["x"], h["y"]) == i]
        assert len(own) == SCAD["esc_pins_in"] + SCAD["esc_pins_out"], len(own)
        r = lambda h: h["x"] * u[0] + h["y"] * u[1]
        t = lambda h: h["x"] * p[0] + h["y"] * p[1]
        rr = sorted({round(r(h), 2) for h in own})
        assert len(rr) == 2 and abs(rr[0] + rr[1] - 2 * SCAD["esc_radius"]) < 0.05, rr
        inner = sorted([h for h in own if round(r(h), 2) == rr[0]], key=t)
        outer = sorted([h for h in own if round(r(h), 2) == rr[1]], key=t)
        assert len(inner) == SCAD["esc_pins_in"]
        cx, cy = SCAD["esc_radius"] * u[0], SCAD["esc_radius"] * u[1]
        fp = new_fp(board, f"J{i + 1}", f"ESC {MOTOR_NAMES[i]} (DYS XSD7A)", VS(cx, cy),
                    "ESC_XSD7A_Headers_1x4_1x3")
        for n, h in enumerate(inner + outer, 1):
            add_pad(fp, n, VS(h["x"], h["y"]), pcbnew.PAD_ATTRIB_PTH, (ESC_PAD, ESC_PAD), h["d"],
                    shape_=pcbnew.PAD_SHAPE_RECT if n in (1, 5) else pcbnew.PAD_SHAPE_CIRCLE)
        ang = math.degrees(math.atan2(u[1], u[0]))
        fp_poly(fp, rect_s(cx, cy, SCAD["esc_l"], SCAD["esc_w"], ang), pcbnew.B_Fab, 0.1)
        fp_poly(fp, rect_s(cx, cy, SCAD["esc_l"] + 4.2, SCAD["esc_w"] + 1.0, ang), pcbnew.F_CrtYd)

    # --- mounting holes (library footprints), sorted by position ---
    cnt = {}
    for h in holes:
        if h["kind"] == "m2" and min(math.hypot(h["x"] - mx, h["y"] - my) for mx, my in MOTORS) < 6:
            continue          # motor screw, already in the motor footprint
        if h["kind"] != "m2":
            continue
        ax, ay = abs(h["x"]), abs(h["y"])
        if math.hypot(ax - SCAD["crad_hole"][0], ay - SCAD["crad_hole"][1]) < 0.1:
            pre, val = "H_CV", "Cover + FC M2x20 bolt"
        elif math.hypot(ax - SCAD["gear_hole"][0], ay - SCAD["gear_hole"][1]) < 0.1:
            pre, val = "H_LG", "Landing gear M2"
        else:
            raise AssertionError(f"unexpected M2 hole {h}")
        cnt[pre] = cnt.get(pre, 0) + 1
        fp = load_fp("MountingHole", "MountingHole_2.2mm_M2")
        fp.SetReference(f"{pre}{cnt[pre]}")
        fp.SetValue(val)
        fp.SetPosition(VS(h["x"], h["y"]))
        fp.Reference().SetLayer(pcbnew.F_Fab)     # close to the board edge
        board.Add(fp)
    assert cnt == {"H_CV": 4, "H_LG": 4}, cnt      # cover + FC standoffs, and the landing-gear skids
    dropped = [h for h in holes if h["kind"] == "jst_ph"]     # J8 is placed on them below

    # --- battery tab pads (scad pcb(): tab_pad x 10 mm at both cell ends, top copper) ---
    fp = new_fp(board, "BT1", "18650 tabs", VS(0, 0), "Battery_18650_TabPads")
    for n, s in ((1, 1), (2, -1)):
        add_pad(fp, n, VS(s * TAB_PAD_X, 0), pcbnew.PAD_ATTRIB_SMD, TAB_PAD_SIZE,
                shape_=pcbnew.PAD_SHAPE_RECT)
    fp_poly(fp, rect_s(0, 0, SCAD["bat_len"], SCAD["bat_d"]), pcbnew.F_Fab, 0.1)
    fp_poly(fp, rect_s(0, 0, 2 * TAB_PAD_X + TAB_PAD_SIZE[0] + 0.5, SCAD["bat_d"] + 0.5), pcbnew.F_CrtYd)

    # --- J5 / J6 female sockets on the BOTTOM: the FC module's J1 / J2 plug in ---
    # Sullins NPPN101BFLD-RC (SMD, 4.6 mm): nylon body, hand-soldered after the frame's reflow.
    for ref, sy in (("J5", 1), ("J6", -1)):
        fp = place_b2b(board, *B2B["socket_fp"], ref,
                       "Sullins NPPN101BFLD-RC 1x10 2.00mm socket (FC " + ("J1" if sy > 0 else "J2") + ")", sy, bottom=True)
        fp.Value().SetVisible(False)

    # --- connectors to the Pi Zero 2 W on the frame top ---
    for ref, lib, fpn, val, (x, y), rot in FRAME_CONN:          # J7 Pi USB, J9 SWD (DNP)
        fp = load_fp(lib, fpn)
        fp.SetReference(ref)
        fp.SetValue(val)
        if "DNP" in val:
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | getattr(pcbnew, "FP_DNP", 0))
        fp.SetPosition(VS(x, y))
        fp.SetOrientationDegrees(rot)
        board.Add(fp)
    ph = sorted(dropped, key=lambda h: h["x"])                 # J8 Pi 5.1 V: JST-PH on the scad's two holes
    assert len(ph) == 2 and abs(ph[0]["y"] - ph[1]["y"]) < 0.01
    fp = load_fp("Connector_JST", "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical")
    fp.SetReference("J8")
    fp.SetValue("Pi 5.1 V: 5V1, GND")
    fp.Reference().SetLayer(pcbnew.F_Fab)
    board.Add(fp)
    fp.SetPosition(VS(ph[0]["x"], ph[0]["y"]))                 # pad 1 is the footprint origin
    p2 = [p for p in fp.Pads() if p.GetNumber() == "2"][0].GetPosition()
    assert abs(p2.x - VS(ph[1]["x"], 0).x) < mm(0.01) and abs(p2.y - VS(0, ph[1]["y"]).y) < mm(0.01), "J8 pads off the DXF holes"

    # --- guides: top side on Dwgs.User, bottom side on Cmts.User ---
    top, bot = pcbnew.Dwgs_User, pcbnew.Cmts_User
    for i, (mx, my) in enumerate(MOTORS):
        circle(board, VS(mx, my), SCAD["prop_d"] / 2, top, 0.1)
        text(board, f"{MOTOR_NAMES[i]} prop 2.5in", VS(mx * 0.78, my * 1.12), top, 1.2)
    poly(board, rect_s(0, 0, SCAD["pi_l"], SCAD["pi_w"]), top, 0.15)
    for sx in (-1, 1):
        for sy in (-1, 1):
            circle(board, VS(sx * SCAD["pi_hole_x"] / 2, sy * SCAD["pi_hole_y"] / 2), 1.375, top)
    text(board, "Pi Zero 2 W (on the battery cover, above the cell)", VS(0, SCAD["pi_w"] / 2 - 2.5), top, 1.0)
    text(board, "18650 cell on top, tabs soldered to BT1", VS(0, -5), top, 1.0)
    poly(board, [VS(x, y) for x, y in fc_outline_pts()], bot, 0.15)
    text(board, f"FC module below ({B2B['standoff']:g} mm printed spacers + M2x20 bolts on H_CV1-4), plugs into J5/J6", VS(0, -23), bot, 1.0)
    pcx, pcy = FC["pico_c"]
    poly(board, rect_s(pcx, pcy, *FC["pico_size"]), bot, 0.1)
    text(board, "Pico 2 W below (~4 mm tall): only low parts here", VS(pcx, pcy - 3), bot, 0.8)
    text(board, "ESC under arm (bottom)", VS(SCAD["esc_radius"] * 0.5, -3), bot, 0.8)
    seg(board, VS(-8, 0), VS(8, 0), top, 0.3)
    seg(board, VS(8, 0), VS(5, 2), top, 0.3)
    seg(board, VS(8, 0), VS(5, -2), top, 0.3)
    text(board, "FRONT (camera, +x)", VS(18, 0), top, 1.2)

    # --- silkscreen ---
    text(board, f"1S Pico2W drone frame r{REVISION}", VS(0, -13.5), pcbnew.F_SilkS, 1.2, 0.18)
    text(board, "FRONT >", VS(30, -13.5), pcbnew.F_SilkS, 1.2, 0.18)
    for i, (mx, my) in enumerate(MOTORS):
        text(board, MOTOR_NAMES[i], VS(mx * 0.62, my * 0.62), pcbnew.F_SilkS, 1.0, 0.15,
             rot=-math.degrees(math.atan2(my, mx)) + (180 if mx < 0 else 0))

    c = finish(board, pcb, name)
    print(f"  imported {len(holes)} holes from the DXF; the {len(dropped)} JST-PH holes carry J8 (Pi 5.1 V)")
    return c


# ---------------------------------------------------------------------------
# FC module
# ---------------------------------------------------------------------------
def build_fc():
    d = os.path.join(ROOT, "FC")
    os.makedirs(d, exist_ok=True)
    name = FC["project"]
    pcb = os.path.join(d, f"{name}.kicad_pcb")
    write_project(os.path.join(d, f"{name}.kicad_pro"), ("VSYS", "VBAT*", "3V3"))
    board = new_board(pcb, FC["title"], FC["thickness"],
                      "Pico 2 W + BMI088 + BMP388 + Flow deck v2 adapter; 30.5 mm M2.5 mount")
    pts = fc_outline_pts()
    poly(board, [VS(x, y) for x, y in pts], pcbnew.Edge_Cuts, 0.1)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    print(f"  FC outline {len(pts)} points, bbox x {min(xs):.2f}..{max(xs):.2f}  y {min(ys):.2f}..{max(ys):.2f}")

    # the four shared M2 holes (cover / frame / landing gear / standoff / FC)
    for n, (hx, hy) in enumerate(FC["holes"], 1):
        fp = load_fp("MountingHole", "MountingHole_2.2mm_M2")
        fp.SetReference(f"H{n}")
        fp.SetValue("M2x20 bolt + 7 mm spacer to frame")
        fp.SetPosition(VS(hx, hy))
        fp.Reference().SetLayer(pcbnew.F_Fab)
        board.Add(fp)

    top, bot = pcbnew.Dwgs_User, pcbnew.Cmts_User
    pcx, pcy = FC["pico_c"]

    # --- U1 Pico 2 W on TOP, micro-USB to the rear (-x), antenna over the notch ---
    u1 = load_fp("KD_Modules", "RPi_Pico_2_W_SMD_Castellated")
    u1.SetReference("U1")
    u1.SetValue("RPi_Pico_2_W")
    u1.SetPosition(VS(pcx, pcy))
    u1.SetOrientationDegrees(90)      # footprint USB (-Y) -> board -X (rear)
    board.Add(u1)
    usb = [p for p in u1.Pads() if p.GetNumber() == ""]
    assert all(p.GetPosition().x < VS(pcx - 20, 0).x for p in usb), "USB must face the rear edge"
    pad = {p.GetNumber(): p for p in u1.Pads()}
    # pin 1 at the USB end; with USB to the rear the pin 1..20 row is on the right (-y)
    assert pad["1"].GetPosition().x < VS(pcx - 20, 0).x and pad["1"].GetPosition().y > VS(0, 0).y
    # The module's underside TP1-3 (USB) and SWD pads are solder pads in its footprint now:
    # USB and SWD go up through J1/J2 to the frame (J7 Pi USB, J9 SWD), no keep-outs needed.

    # --- P1 / P2 Crazyflie deck rows on the BOTTOM, pin 1 at the front (+x) ---
    # The Flow deck v2 carries the Bitcraze female deck connectors (SMD, 2.1 mm high) on its
    # top, so the FC gets MALE 1x10 2.00 mm SMD headers pointing down (SMD: no tails up into
    # the Pico's lands on the top side).
    dcx, dcy = FC["deck_c"]
    for ref, sy, names in (("P1", 1, DECK_LEFT), ("P2", -1, DECK_RIGHT)):
        fp = place_b2b(board, "Connector_PinHeader_2.00mm", "PinHeader_1x10_P2.00mm_Vertical_SMD_Pin1Left", ref,
                       "Flow deck " + ("left (P1)" if sy > 0 else "right (P2)") + ", male 1x10 2.00mm SMD", sy,
                       bottom=True, row_y=FC["deck_rows"] / 2)
        fp.Value().SetVisible(False)
        fp.Reference().SetLayer(pcbnew.B_Fab)

    # --- sensors on the BOTTOM, in the cavity between the deck rows under the Flow deck ---
    # BMI088 at the centre (CG, Flow deck axis), its long side along x so the package axes line
    # up with the drone's; BMP388 behind it, sheltered from prop wash and light by the deck
    # above (design doc: shield the baro from airflow and light). Decoupling as Bolt 1.1.
    for ref, lib, fpn, val, (x, y), rot in FC["sensors"]:
        fp = load_fp(lib, fpn)
        fp.SetReference(ref)
        fp.SetValue(val)
        board.Add(fp)
        fp.Flip(fp.GetPosition(), True)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(VS(x, y))
        fp.Reference().SetLayer(pcbnew.B_Fab)
        assert all(p.IsOnLayer(pcbnew.B_Cu) for p in fp.Pads())

    # --- support passives (stage 2/3): sensor supply filter, pull-ups, DShot series resistors ---
    for ref, lib, fpn, val, (x, y), rot, side in FC["passives"]:
        fp = load_fp(lib, fpn)
        fp.SetReference(ref)
        fp.SetValue(val)
        board.Add(fp)
        if side == "B":
            fp.Flip(fp.GetPosition(), True)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(VS(x, y))
        fp.Reference().SetLayer(pcbnew.B_Fab if side == "B" else pcbnew.F_Fab)
        fp.Value().SetVisible(False)
        assert all(p.IsOnLayer(pcbnew.B_Cu if side == "B" else pcbnew.F_Cu) for p in fp.Pads())

    # --- J1 / J2 male headers on TOP: plug up into the frame's J5 / J6 ---
    # Wurth 62001011121: its datasheet asks for 0.90 mm holes (the stock footprint has 0.8 mm).
    for ref, sy in (("J1", 1), ("J2", -1)):
        fp = place_b2b(board, "Connector_PinHeader_2.00mm", "PinHeader_1x10_P2.00mm_Vertical", ref,
                       "Wurth 62001011121 header 1x10 2.00mm male (to frame " + ("J5" if sy > 0 else "J6") + ")", sy, bottom=False)
        for p in fp.Pads():
            p.SetDrillSize(pcbnew.VECTOR2I(mm(B2B["male_hole"]), mm(B2B["male_hole"])))
        fp.Value().SetVisible(False)
        fp.Reference().SetLayer(pcbnew.F_Fab)      # no room for it on the trimmed outline
    text(board, f"FC hangs on 4 M2x20 bolts through {B2B['standoff']:g} mm printed spacers; J1/J2 plug into the frame", VS(0, -19.5), top, 0.6)

    # --- J9 SWD (DNP) on the BOTTOM at the rear edge, opening towards the edge (-x) ---
    ref, fpn, val, (x, y) = FC["swd"]
    fp = load_fp("Connector_JST", fpn)
    fp.SetReference(ref)
    fp.SetValue(val)
    fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)
    board.Add(fp)
    fp.Flip(fp.GetPosition(), True)
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(VS(x, y))
        sig = [p.GetPosition() for p in fp.Pads() if p.GetNumber() != "MP"]
        mp = [p.GetPosition() for p in fp.Pads() if p.GetNumber() == "MP"]
        mx = sum(v.x for v in mp) / len(mp)
        sx = sum(v.x for v in sig) / len(sig)
        if mx < sx and abs(mp[0].x - mp[1].x) < mm(0.01):     # mounting pads (the opening) nearer the rear edge
            break
    else:
        raise AssertionError("J9: no orientation puts its opening at the rear edge")
    fp.Reference().SetLayer(pcbnew.B_Fab)
    fp.Value().SetVisible(False)

    # --- SW1 BOOTSEL button on the BOTTOM next to J9, pressed from below (Pico TP6 -> GND) ---
    ref, lib, fpn, val, (x, y), rot = FC["bootsel"]
    fp = load_fp(lib, fpn)
    fp.SetReference(ref)
    fp.SetValue(val)
    board.Add(fp)
    fp.Flip(fp.GetPosition(), True)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(VS(x, y))
    fp.Reference().SetLayer(pcbnew.B_Fab)
    fp.Reference().SetPosition(VS(x, y + 1.9))      # Fab ref above the body, the BOOT silk below it
    fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)))
    for g in fp.GraphicalItems():                    # the footprint's own ${REFERENCE} Fab text sits on BOOT
        if isinstance(g, getattr(pcbnew, "FP_TEXT", pcbnew.PCB_TEXT)) and g.GetText() == "${REFERENCE}":
            g.SetVisible(False)
    fp.Value().SetVisible(False)
    assert all(p.IsOnLayer(pcbnew.B_Cu) for p in fp.Pads())
    text(board, "BOOT", VS(x, y - 2.5), pcbnew.B_SilkS, 0.8, 0.15)

    # --- guides ---
    poly(board, rect_s(dcx, dcy, *FC["deck_board"]), bot, 0.15)
    text(board, "Flow deck v2 (below, on P1/P2)", VS(dcx, dcy + 5), bot, 0.8)
    text(board, "BMI088 + BMP388 under the Flow deck", VS(dcx, dcy - 4), bot, 0.7)
    text(board, "bottom: support ICs (LDO, filters)", VS(-19.5, 0), bot, 0.8, rot=90)
    poly(board, rect_s(-19.5, 0, 15, 22), bot, 0.1)
    seg(board, VS(-6, -13), VS(6, -13), top, 0.3)
    seg(board, VS(6, -13), VS(4, -11.5), top, 0.3)
    seg(board, VS(6, -13), VS(4, -14.5), top, 0.3)
    text(board, FC["silk_name"], VS(0, -12.9), pcbnew.F_SilkS, 0.8, 0.15)  # strip between the Pico and J2 (J1 side: DShot resistors)
    text(board, FC["silk_name"], VS(-18.5, 0), pcbnew.B_SilkS, 0.8, 0.15, rot=90)
    text(board, "< FRONT", VS(17.5, -10.0), pcbnew.B_SilkS, 0.8, 0.15)    # reads from below: front is to the left
    fc_electrical(board)
    return finish(board, pcb, name)


# ---------------------------------------------------------------------------
# FC electrical: nets (fc_design.py), hand routes (routes_fc.py), router I/O, GND pours
# ---------------------------------------------------------------------------
def assign_nets(board, nets):
    names = {}
    for net in nets:
        ni = pcbnew.NETINFO_ITEM(board, net)
        board.Add(ni)
        names[net] = ni
    missing = []
    for net, conns in nets.items():
        for ref, pin in conns:
            fp = board.FindFootprintByReference(ref)
            pads = [p for p in fp.Pads() if p.GetNumber() == pin] if fp else []
            if not pads:
                missing.append(f"{ref}.{pin}")
            for p in pads:
                p.SetNet(names[net])
    if missing:
        raise SystemExit(f"pads not found for nets: {missing}")
    return names


def add_hand_routes(board):
    import importlib
    import routes_fc
    importlib.reload(routes_fc)
    lay = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
    for net, layer, w, pts in routes_fc.TRACKS:
        for a, b in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(VS(*a))
            t.SetEnd(VS(*b))
            t.SetWidth(mm(w))
            t.SetLayer(lay[layer])
            t.SetNet(board.FindNet(net))
            board.Add(t)
    for net, x, y, d, drill in routes_fc.VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(VS(x, y))
        v.SetWidth(mm(d))
        v.SetDrill(mm(drill))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(board.FindNet(net))
        board.Add(v)
    return len(routes_fc.TRACKS), len(routes_fc.VIAS)


def _bbox(item):
    b = item.GetBoundingBox()
    return [pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetTop()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom())]


def export_geom(board, nets, path):
    """Router input (router.py): outline, pads, keep-outs, hand-routed tracks / vias, nets (KiCad mm)."""
    cu = {pcbnew.F_Cu: "F", pcbnew.B_Cu: "B"}
    pads = [{"ref": fp.GetReference(), "pin": pd.GetNumber(), "net": pd.GetNetname(),
             "layers": [n for l, n in cu.items() if pd.IsOnLayer(l)], "bbox": _bbox(pd)}
            for fp in board.GetFootprints() for pd in fp.Pads()]
    tracks, vias = [], []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            vias.append({"net": t.GetNetname(), "x": pcbnew.ToMM(p.x), "y": pcbnew.ToMM(p.y),
                         "d": pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))})
        else:
            a, b = t.GetStart(), t.GetEnd()
            tracks.append({"net": t.GetNetname(), "layer": cu[t.GetLayer()], "x1": pcbnew.ToMM(a.x), "y1": pcbnew.ToMM(a.y),
                           "x2": pcbnew.ToMM(b.x), "y2": pcbnew.ToMM(b.y), "w": pcbnew.ToMM(t.GetWidth())})
    outline = [to_kicad(x, y) for x, y in fc_outline_pts()]
    js = {"outline": outline, "pads": pads, "shapes": [], "keepouts": [], "tracks": tracks, "vias": vias,
          "nets": {n: {"pins": c, "power": n in fc_design.POWER_NETS} for n, c in nets.items()}}
    os.makedirs(BUILD, exist_ok=True)
    json.dump(js, open(path, "w"))
    print(f"  geometry: {len(pads)} pads, {len(tracks)} tracks, {len(vias)} vias -> {os.path.relpath(path, ROOT)}")


def import_routes(board, path):
    data = json.load(open(path))
    lay = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
    for t in data["tracks"]:
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(V(t["x1"], t["y1"]))
        tr.SetEnd(V(t["x2"], t["y2"]))
        tr.SetWidth(mm(t["w"]))
        tr.SetLayer(lay[t["layer"]])
        tr.SetNet(board.FindNet(t["net"]))
        board.Add(tr)
    for v in data["vias"]:
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(V(v["x"], v["y"]))
        via.SetWidth(mm(v["d"]))
        via.SetDrill(mm(v["drill"]))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(board.FindNet(v["net"]))
        board.Add(via)
    # track ends inside a pad's box but off its copper (round pads): extend to the pad centre
    pads = [(pd, _bbox(pd)) for fp in board.GetFootprints() for pd in fp.Pads() if pd.GetNetname()]
    fixed = 0
    for t in data["tracks"]:
        for x, y in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
            for pd, (x0, y0, x1, y1) in pads:
                if pd.GetNetname() != t["net"] or not (x0 <= x <= x1 and y0 <= y <= y1) or not pd.IsOnLayer(lay[t["layer"]]):
                    continue
                if pd.HitTest(V(x, y)):
                    break
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(V(x, y))
                tr.SetEnd(pd.GetPosition())
                tr.SetWidth(mm(min(t["w"], 0.25)))
                tr.SetLayer(lay[t["layer"]])
                tr.SetNet(board.FindNet(t["net"]))
                board.Add(tr)
                fixed += 1
                break
    print(f"  router: {len(data['tracks'])} segments, {len(data['vias'])} vias; failed {data['failed']}; "
          f"{fixed} ends extended to pad centres")


def gnd_pours(board):
    """GND pour on both copper layers over the FC outline (0.25 mm clearance, thermal reliefs)."""
    gnd = board.FindNet("GND")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetLocalClearance(mm(0.25))
        z.SetMinThickness(mm(0.25))
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.4))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in fc_outline_pts():
            ol.Append(VS(x, y))
        board.Add(z)
    try:                                  # KiCad 7; KiCad 8+ refill through kicad-cli in finish()
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    except Exception as e:                # noqa: BLE001
        print(f"  zone fill deferred to kicad-cli ({e})")


def stitch_vias(board, pitch=1.2, d=0.6, drill=0.3, spacing=2.4):
    """GND stitching vias on a grid wherever no foreign copper, hole or edge is near: they tie the two GND pours
    together and reach pour islands that tracks have cut off. Returns the number placed."""
    import numpy as np
    def segd(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        L = dx * dx + dy * dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L))
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))
    obst = []                                    # (kind, data, clearance radius beyond the via edge)
    for fp in board.GetFootprints():
        for pd in fp.Pads():
            bb = _bbox(pd)
            same = pd.GetNetname() == "GND"
            hole = pd.GetDrillSize().x > 0
            if same and not hole:
                continue
            obst.append(("box", bb, 0.25 if not same else 0.3))
    for t in board.GetTracks():
        if t.GetNetname() == "GND" and t.GetClass() != "PCB_VIA":
            continue
        if t.GetClass() == "PCB_VIA":
            p_ = t.GetPosition()
            obst.append(("pt", (pcbnew.ToMM(p_.x), pcbnew.ToMM(p_.y), pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) / 2), 0.3))
        else:
            a_, b_ = t.GetStart(), t.GetEnd()
            obst.append(("seg", (pcbnew.ToMM(a_.x), pcbnew.ToMM(a_.y), pcbnew.ToMM(b_.x), pcbnew.ToMM(b_.y),
                                 pcbnew.ToMM(t.GetWidth()) / 2), 0.25))
    outline = [to_kicad(x, y) for x, y in fc_outline_pts()]
    def inside(x, y):
        c = False
        for (x1, y1), (x2, y2) in zip(outline, outline[1:] + outline[:1]):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        return c
    def edge_d(x, y):
        return min(segd(x, y, x1, y1, x2, y2) for (x1, y1), (x2, y2) in zip(outline, outline[1:] + outline[:1]))
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    gnd = board.FindNet("GND")
    placed = []
    r = d / 2
    for x in np.arange(min(xs) + 1, max(xs) - 1, pitch):
        for y in np.arange(min(ys) + 1, max(ys) - 1, pitch):
            if not inside(x, y) or edge_d(x, y) < r + 0.5:
                continue
            ok = True
            for kind, o, c in obst:
                if kind == "box":
                    x0, y0, x1, y1 = o
                    dd = math.hypot(max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1))
                    ok = dd >= r + c
                elif kind == "pt":
                    ok = math.hypot(x - o[0], y - o[1]) >= r + o[2] + c
                else:
                    ok = segd(x, y, *o[:4]) >= r + o[4] + c
                if not ok:
                    break
            if ok and all(math.hypot(x - a_, y - b_) >= spacing for a_, b_ in placed):
                placed.append((x, y))
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(V(float(x), float(y)))
                v.SetWidth(mm(d))
                v.SetDrill(mm(drill))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNet(gnd)
                board.Add(v)
    return len(placed)


FC_GEOM = os.path.join(BUILD, "fc_geometry.json")
FC_ROUTES = os.path.join(BUILD, "fc_routes.json")


def fc_electrical(board):
    if not ({"geom", "finish", "nets"} & set(sys.argv)):
        return                                   # bare board (stage 1 behaviour)
    nets = fc_design.build_nets()
    assign_nets(board, nets)
    n_t, n_v = add_hand_routes(board)
    print(f"  nets: {len(nets)}; hand routes: {n_t} tracks, {n_v} vias")
    if "geom" in sys.argv:
        export_geom(board, nets, FC_GEOM)
    if "finish" in sys.argv:
        import_routes(board, FC_ROUTES)
        print(f"  GND stitching vias: {stitch_vias(board)}")
        gnd_pours(board)


if __name__ == "__main__":
    which = [a for a in sys.argv[1:] if a in ("frame", "fc")] or ["frame", "fc"]
    ok = True
    for w in which:
        c = {"frame": build_frame, "fc": build_fc}[w]()
        ok &= all(v == 0 for v in c.values()) and len(c) == 3
    print("DRC OK" if ok else "DRC FAILED")
    sys.exit(0 if ok else 1)
