#!/usr/bin/python3
"""
Generate the bare boards (run with the system interpreter, which has pcbnew):

    /usr/bin/python3 gen_pcb.py            # both boards
    /usr/bin/python3 gen_pcb.py frame|fc

Each board gets: .kicad_pro (rules), .kicad_pcb (outline, holes, fixed pads,
placement guides on Dwgs.User = top side / Cmts.User = bottom side), and a DRC
report in ../build/<board>_drc.txt.
"""

import json
import math
import os
import sys

import pcbnew

import dxf_import
from gen_libs import PICO_TP, PICO_SWD
from design import (FC, FRAME, LIB, DECK_LEFT, DECK_RIGHT, B2B, B2B_PIN_X, MOTORS, MOTOR_NAMES, SCAD, ESC_PAD, TAB_PAD_SIZE, TAB_PAD_X,
                    REVISION, DATE, to_kicad, uid, ORIGIN_X, ORIGIN_Y)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
BUILD = os.path.join(ROOT, "build")
KFP = "/usr/share/kicad/footprints"

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
                                "lib_footprint_mismatch": "ignore"},
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
    fp = pcbnew.FootprintLoad(os.path.join(KFP, f"{lib}.pretty"), name)
    if fp is None:
        raise RuntimeError(f"footprint {lib}:{name} not found")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def load_prj_fp(name):
    fp = pcbnew.FootprintLoad(os.path.join(ROOT, f"{LIB}.pretty"), name)
    if fp is None:
        raise RuntimeError(f"footprint {LIB}:{name} not found - run gen_libs.py")
    fp.SetFPID(pcbnew.LIB_ID(LIB, name))
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


def place_b2b(board, lib, name, ref, value, row_sign, bottom):
    """Place a 1x10 board-to-board part so that pad k sits at scad
    (B2B_PIN_X[k-1], row_sign * row_y), on the given side. Tries the four
    orientations and keeps the one that matches (asserted)."""
    y = row_sign * B2B["row_y"]
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
           all(abs(got[k].y - want[k].y) < mm(1.7) for k in want):
            assert all(p.IsOnLayer(pcbnew.B_Cu if bottom else pcbnew.F_Cu) for p in fp.Pads())
            return fp
    raise AssertionError(f"{ref}: no orientation puts pin k at x = 9 - 2(k-1)")


def new_fp(board, ref, value, pos, name):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetFPID(pcbnew.LIB_ID("Drone_1S", name))
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(pos)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    for f in (fp.Reference(), fp.Value()):
        f.SetLayer(pcbnew.F_Fab)
    board.Add(fp)
    return fp


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
    p.SetLocalCoord()          # KiCad 7: store pos0 (footprint-relative) from the absolute position
    return p


def fp_circle(fp, c, r, layer, w=0.05):
    s = pcbnew.FP_SHAPE(fp, pcbnew.SHAPE_T_CIRCLE)
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    fp.Add(s)
    s.SetCenter(c)
    s.SetEnd(pcbnew.VECTOR2I(c.x + mm(r), c.y))
    s.SetLocalCoord()


def fp_poly(fp, pts, layer, w=0.05):
    for i in range(len(pts)):
        s = pcbnew.FP_SHAPE(fp, pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(layer)
        s.SetWidth(mm(w))
        fp.Add(s)
        s.SetStart(pts[i - 1])
        s.SetEnd(pts[i])
        s.SetLocalCoord()


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


def finish(board, path, name):
    os.makedirs(BUILD, exist_ok=True)
    pcbnew.SaveBoard(path, board)
    board = pcbnew.LoadBoard(path)
    rpt = os.path.join(BUILD, f"{name}_drc.txt")
    pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(rpt).read()
    import re
    counts = {k: int(v) for v, k in re.findall(r"\*\* Found (\d+) (DRC violations|unconnected pads|Footprint errors)", txt)}
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

    # --- mounting holes (library footprints) ---
    lib_hole = {"fc_mount": ("MountingHole", "MountingHole_2.7mm_M2.5", "H_FC"),
                "m2": ("MountingHole", "MountingHole_2.2mm_M2", "H_CV")}
    cnt = {}
    for h in holes:
        if h["kind"] == "m2" and min(math.hypot(h["x"] - mx, h["y"] - my) for mx, my in MOTORS) < 6:
            continue          # motor screw, already in the motor footprint
        if h["kind"] not in lib_hole:
            continue
        lib, fpn, pre = lib_hole[h["kind"]]
        cnt[pre] = cnt.get(pre, 0) + 1
        fp = load_fp(lib, fpn)
        fp.SetReference(f"{pre}{cnt[pre]}")
        fp.SetValue("FC M2.5" if pre == "H_FC" else "Cover/gear M2")
        fp.SetPosition(VS(h["x"], h["y"]))
        board.Add(fp)
    assert cnt == {"H_FC": 4, "H_CV": 4}, cnt
    dropped = [h for h in holes if h["kind"] == "jst_ph"]

    # --- battery tab pads (scad pcb(): tab_pad x 10 mm at both cell ends, top copper) ---
    fp = new_fp(board, "BT1", "18650 tabs", VS(0, 0), "Battery_18650_TabPads")
    for n, s in ((1, 1), (2, -1)):
        add_pad(fp, n, VS(s * TAB_PAD_X, 0), pcbnew.PAD_ATTRIB_SMD, TAB_PAD_SIZE,
                shape_=pcbnew.PAD_SHAPE_RECT)
    fp_poly(fp, rect_s(0, 0, SCAD["bat_len"], SCAD["bat_d"]), pcbnew.F_Fab, 0.1)
    fp_poly(fp, rect_s(0, 0, 2 * TAB_PAD_X + TAB_PAD_SIZE[0] + 0.5, SCAD["bat_d"] + 0.5), pcbnew.F_CrtYd)

    # --- J5 / J6 female sockets on the BOTTOM: the FC module's J1 / J2 plug in ---
    for ref, sy in (("J5", 1), ("J6", -1)):
        fp = place_b2b(board, "Connector_PinSocket_2.00mm", "PinSocket_1x10_P2.00mm_Vertical_SMD_Pin1Left", ref,
                       "Socket 1x10 2.00mm female SMD (FC " + ("J1" if sy > 0 else "J2") + ")", sy, bottom=True)
        fp.Value().SetVisible(False)

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
    poly(board, rect_s(0, 0, *FC["size"]), bot, 0.15)
    text(board, f"FC module below on {B2B['standoff']:g} mm M2.5 standoffs, plugs into J5/J6", VS(0, -FC["size"][1] / 2 - 1.5), bot, 1.0)
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
    print(f"  imported {len(holes)} holes from the DXF; dropped {len(dropped)} JST-PH holes "
          f"(Bolt-era J1/J3 connectors, placed again as real footprints later)")
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
    L_, W_ = FC["size"]
    r = FC["corner_r"]
    nw, nd = FC["notch"]
    x0, x1, y0, y1 = -L_ / 2, L_ / 2, -W_ / 2, W_ / 2
    pico_end = FC["pico_c"][0] + FC["pico_size"][0] / 2       # antenna end of the Pico
    nx = pico_end - nd                                          # notch bottom
    k = r * (1 - 1 / math.sqrt(2))
    # outline, counter-clockwise in scad coordinates, starting at the rear-right corner
    E = pcbnew.Edge_Cuts
    seg(board, VS(x0 + r, y0), VS(x1 - r, y0))
    arc(board, VS(x1 - r, y0), VS(x1 - k, y0 + k), VS(x1, y0 + r))
    seg(board, VS(x1, y0 + r), VS(x1, -nw / 2))
    poly_pts = [VS(x1, -nw / 2), VS(nx, -nw / 2), VS(nx, nw / 2), VS(x1, nw / 2)]
    for a, b in zip(poly_pts, poly_pts[1:]):
        seg(board, a, b)
    seg(board, VS(x1, nw / 2), VS(x1, y1 - r))
    arc(board, VS(x1, y1 - r), VS(x1 - k, y1 - k), VS(x1 - r, y1))
    seg(board, VS(x1 - r, y1), VS(x0 + r, y1))
    arc(board, VS(x0 + r, y1), VS(x0 + k, y1 - k), VS(x0, y1 - r))
    seg(board, VS(x0, y1 - r), VS(x0, y0 + r))
    arc(board, VS(x0, y0 + r), VS(x0 + k, y0 + k), VS(x0 + r, y0))

    for n, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, -1), (-1, 1)), 1):
        fp = load_fp("MountingHole", "MountingHole_2.7mm_M2.5")
        fp.SetReference(f"H{n}")
        fp.SetValue("M2.5 to frame")
        fp.SetPosition(VS(sx * FC["holes"] / 2, sy * FC["holes"] / 2))
        fp.Reference().SetLayer(pcbnew.F_Fab)     # silk would hang off the board edge
        board.Add(fp)

    top, bot = pcbnew.Dwgs_User, pcbnew.Cmts_User
    pcx, pcy = FC["pico_c"]

    # --- U1 Pico 2 W on TOP, micro-USB to the rear (-x), antenna over the notch ---
    u1 = load_prj_fp("RPi_Pico_2_W_SMD_Castellated")
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
    # keep top copper away from the module's underside test points / SWD pads
    # (datasheet: OK to void copper under unused test points)
    ang = math.radians(90)
    def mod2scad(fx, fy):       # footprint coords (KiCad, y down) -> scad, after the 90 deg rotation
        kx = fx * math.cos(ang) + fy * math.sin(ang)
        ky = -fx * math.sin(ang) + fy * math.cos(ang)
        return pcx + kx, pcy - ky
    for i, (fx, fy) in enumerate(PICO_TP + PICO_SWD):
        x, y = mod2scad(fx, fy)
        rule_area(board, rect_s(x, y, 2.4, 2.4), pcbnew.F_Cu, f"KEEPOUT_PICO_{'TP%d' % (i + 1) if i < 3 else 'SWD%d' % (i - 2)}")

    # --- P1 / P2 Crazyflie deck rows on the BOTTOM: pin 1 at the front (+x) ---
    dcx, dcy = FC["deck_c"]
    for ref, sy, names in (("P1", 1, DECK_LEFT), ("P2", -1, DECK_RIGHT)):
        fp = load_prj_fp("CF_Deck_1x10_P2.00mm_SMD")
        fp.SetReference(ref)
        fp.SetValue("CF deck " + ("left" if sy > 0 else "right"))
        fp.SetPosition(VS(dcx, dcy + sy * FC["deck_rows"] / 2))
        board.Add(fp)
        fp.Flip(fp.GetPosition(), True)       # to B.Cu: mirrors x (pin 1 -> +x, the front)
        for p in fp.Pads():
            k = int(p.GetNumber())
            want = VS(dcx + 9 - 2 * (k - 1), 0).x
            assert abs(p.GetPosition().x - want) < mm(0.01), (ref, k, pcbnew.ToMM(p.GetPosition().x))
            assert p.IsOnLayer(pcbnew.B_Cu)
        fp.Value().SetVisible(False)
        fp.Reference().SetPosition(VS(dcx - 12.3, dcy + sy * FC["deck_rows"] / 2))   # rear end of the row

    # --- J1 / J2 male headers on TOP: plug up into the frame's J5 / J6 ---
    for ref, sy in (("J1", 1), ("J2", -1)):
        fp = place_b2b(board, "Connector_PinHeader_2.00mm", "PinHeader_1x10_P2.00mm_Vertical", ref,
                       "Header 1x10 2.00mm male (to frame " + ("J5" if sy > 0 else "J6") + ")", sy, bottom=False)
        fp.Value().SetVisible(False)
    text(board, f"FC hangs on {B2B['standoff']:g} mm M2.5 standoffs; J1/J2 plug into the frame", VS(0, -16.9), top, 0.6)

    # --- guides ---
    poly(board, rect_s(dcx, dcy, *FC["deck_board"]), bot, 0.15)
    text(board, "Flow deck v2 (below, on P1/P2)", VS(dcx, dcy + 5), bot, 0.8)
    poly(board, rect_s(dcx, dcy, 14, 14), bot, 0.1)
    text(board, "BMI088 here (bottom, centre = CG)", VS(dcx, dcy - 1), bot, 0.7)
    text(board, "bottom: ICs + deck", VS(-19, 0), bot, 0.8, rot=90)
    seg(board, VS(-6, -13), VS(6, -13), top, 0.3)
    seg(board, VS(6, -13), VS(4, -11.5), top, 0.3)
    seg(board, VS(6, -13), VS(4, -14.5), top, 0.3)
    text(board, f"FC r{REVISION}", VS(-21.5, 15.2), pcbnew.F_SilkS, 0.8, 0.15)
    text(board, "FRONT >", VS(-21.5, -15.2), pcbnew.F_SilkS, 0.8, 0.15)
    text(board, f"1S Pico2W FC r{REVISION} bottom", VS(-24.5, 0), pcbnew.B_SilkS, 0.8, 0.12, rot=90)
    return finish(board, pcb, name)


if __name__ == "__main__":
    which = sys.argv[1:] or ["frame", "fc"]
    ok = True
    for w in which:
        c = {"frame": build_frame, "fc": build_fc}[w]()
        ok &= all(v == 0 for v in c.values()) and len(c) == 3
    print("DRC OK" if ok else "DRC FAILED")
    sys.exit(0 if ok else 1)
