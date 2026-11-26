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
from design import (FC, FRAME, MOTORS, MOTOR_NAMES, SCAD, ESC_PAD, TAB_PAD_SIZE, TAB_PAD_X,
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
    text(board, "FC module (bottom, M2.5 standoffs)", VS(0, -FC["size"][1] / 2 - 1.5), bot, 1.0)
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
        board.Add(fp)

    top, bot = pcbnew.Dwgs_User, pcbnew.Cmts_User
    pcx, pcy = FC["pico_c"]
    pl, pw = FC["pico_size"]
    poly(board, rect_s(pcx, pcy, pl, pw), top, 0.15)
    text(board, "Pico 2 W 51 x 21 (placement guide)", VS(pcx - 4, 0), top, 1.0)
    text(board, "USB", VS(x0 + 3, 0), top, 1.0, rot=90)
    text(board, "antenna keep-out (notch)", VS(nx - 3, 0), top, 0.8, rot=90)
    for sy in (-1, 1):
        y = sy * FC["deck_rows"] / 2
        poly(board, rect_s(0, y, 25.4, 2.54), bot, 0.1)
    text(board, "Crazyflie deck rows 2 x 1x10, 17 mm (Flow deck v2, bottom)", VS(0, -W_ / 2 + 1.8), bot, 0.8)
    seg(board, VS(-6, -13), VS(6, -13), top, 0.3)
    seg(board, VS(6, -13), VS(4, -11.5), top, 0.3)
    seg(board, VS(6, -13), VS(4, -14.5), top, 0.3)
    text(board, f"1S Pico2W FC r{REVISION}", VS(-4, 12.8), pcbnew.F_SilkS, 1.0, 0.15)
    text(board, "FRONT >", VS(-4, -12.8), pcbnew.F_SilkS, 1.0, 0.15)
    return finish(board, pcb, name)


if __name__ == "__main__":
    which = sys.argv[1:] or ["frame", "fc"]
    ok = True
    for w in which:
        c = {"frame": build_frame, "fc": build_fc}[w]()
        ok &= all(v == 0 for v in c.values()) and len(c) == 3
    print("DRC OK" if ok else "DRC FAILED")
    sys.exit(0 if ok else 1)
