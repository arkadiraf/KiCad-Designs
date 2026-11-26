#!/usr/bin/python3
"""Generate / finish the Pico Alvik Adapter PCB with the KiCad pcbnew API.

  gen_pcb.py place    -> writes .kicad_pro + placed, unrouted .kicad_pcb + .dsn
  gen_pcb.py geom     -> dumps pads/outline/keep-outs to build/geometry.json
                         (input of tools/router.py)
  gen_pcb.py finish   -> imports build/routes.json (tools/router.py) or a
                         Freerouting .ses, adds GND pours, fills, writes DRC

Must run with the system python that provides the `pcbnew` module.
"""

import json
import os
import re
import sys

import pcbnew
from design import (PROJECT, LIB, COMPONENTS, POWER_NETS, build_nets, uid,
                    BX0, BY0, BOARD_W, BOARD_H, PICO_C, NANO_C, NOTCH_W, NOTCH_H)

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
PCB = os.path.join(PRJ, f"{PROJECT}.kicad_pcb")
PRO = os.path.join(PRJ, f"{PROJECT}.kicad_pro")
OUT = os.path.join(PRJ, "build")
DSN = os.path.join(OUT, f"{PROJECT}.dsn")
SES = os.path.join(OUT, f"{PROJECT}.ses")
KFP = "/usr/share/kicad/footprints"

mm = pcbnew.FromMM
V = pcbnew.VECTOR2I_MM

CX = BX0 + BOARD_W / 2

# bottom side passive placement (top-view coordinates) and silk labels
BOTTOM_PARTS = {
    #  ref    x      y      rot   label
    "C1":  (CX,   106.0,  0,   ""),
    "JP2": (CX,   110.4,  0,   "3V3"),
    "JP3": (CX,   130.8,  0,   "RST"),
    "D1":  (CX,   135.6,  0,   "D1"),
}


# ---------------------------------------------------------------------------
def write_project():
    patterns = [{"netclass": "Power", "pattern": n} for n in sorted(POWER_NETS)]
    pro = {
        "board": {
            "design_settings": {
                "defaults": {
                    "board_outline_line_width": 0.1,
                    "copper_line_width": 0.2,
                    "copper_text_size_h": 1.5, "copper_text_size_v": 1.5,
                    "copper_text_thickness": 0.3,
                    "silk_line_width": 0.12,
                    "silk_text_size_h": 0.8, "silk_text_size_v": 0.8,
                    "silk_text_thickness": 0.12,
                },
                "rules": {
                    "min_clearance": 0.15,
                    "min_track_width": 0.15,
                    "min_via_annular_width": 0.1,
                    "min_via_diameter": 0.5,
                    "min_through_hole_diameter": 0.3,
                    "min_hole_to_hole": 0.25,
                    "min_hole_clearance": 0.25,
                    "min_copper_edge_clearance": 0.25,
                    "min_silk_clearance": 0.0,
                    "min_text_height": 0.6,
                    "min_text_thickness": 0.1,
                    "solder_mask_to_copper_clearance": 0.0,
                },
                "track_widths": [0.0, 0.25, 0.4, 0.5],
                "via_dimensions": [{"diameter": 0.0, "drill": 0.0},
                                   {"diameter": 0.6, "drill": 0.3},
                                   {"diameter": 0.8, "drill": 0.4}],
                "rule_severities": {
                    "silk_overlap": "ignore",
                    "silk_over_copper": "warning",
                    "lib_footprint_issues": "ignore",
                    "lib_footprint_mismatch": "ignore",
                },
            },
        },
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [
                {"name": "Default", "clearance": 0.2, "track_width": 0.25,
                 "via_diameter": 0.6, "via_drill": 0.3,
                 "microvia_diameter": 0.3, "microvia_drill": 0.1,
                 "diff_pair_gap": 0.25, "diff_pair_width": 0.2, "diff_pair_via_gap": 0.25,
                 "bus_width": 12, "wire_width": 6, "line_style": 0,
                 "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"},
                {"name": "Power", "clearance": 0.2, "track_width": 0.5,
                 "via_diameter": 0.8, "via_drill": 0.4,
                 "microvia_diameter": 0.3, "microvia_drill": 0.1,
                 "diff_pair_gap": 0.25, "diff_pair_width": 0.2, "diff_pair_via_gap": 0.25,
                 "bus_width": 12, "wire_width": 6, "line_style": 0,
                 "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"},
            ],
            "meta": {"version": 3},
            "net_colors": None,
            "netclass_assignments": None,
            "netclass_patterns": patterns,
        },
        "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [[uid("root-sheet"), ""]],
        "text_variables": {},
    }
    with open(PRO, "w") as f:
        json.dump(pro, f, indent=2)


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = os.path.join(PRJ, f"{LIB}.pretty") if lib == LIB else os.path.join(KFP, f"{lib}.pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError(f"footprint {fpid} not found")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def seg(board, x1, y1, x2, y2, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(x1, y1))
    s.SetEnd(V(x2, y2))
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    board.Add(s)


def board_outline_pts():
    x0, y0, x1, y1 = BX0, BY0, BX0 + BOARD_W, BY0 + BOARD_H
    nx0, nx1, ny = CX - NOTCH_W / 2, CX + NOTCH_W / 2, y1 - NOTCH_H
    return [(x0, y0), (x1, y0), (x1, y1), (nx1, y1), (nx1, ny), (nx0, ny), (nx0, y1), (x0, y1)]


def add_text(board, txt, x, y, layer, size=0.8, rot=0, mirror=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(V(x, y))
    t.SetLayer(layer)
    t.SetTextSize(V(size, size))
    t.SetTextThickness(mm(0.12 if size < 1 else 0.15))
    if rot:
        t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    t.SetMirrored(mirror)
    board.Add(t)


def add_rule_area(board, pts, layer, name):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetLayer(layer)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(V(x, y))
    board.Add(z)


def rect_pts(cx, cy, w, h):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
            (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


# ---------------------------------------------------------------------------
def place():
    os.makedirs(OUT, exist_ok=True)
    write_project()
    if os.path.exists(PCB):
        os.remove(PCB)
    board = pcbnew.NewBoard(PCB)
    board.SetCopperLayerCount(2)

    tb = board.GetTitleBlock()
    tb.SetTitle("Pico Alvik Adapter")
    tb.SetRevision("1.5")
    tb.SetDate("2026-11-26")
    tb.SetCompany("KiCad-Designs")
    tb.SetComment(0, "Raspberry Pi Pico W carrier in Arduino Nano form factor for the Arduino Alvik")

    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))

    # nets
    nets = build_nets()
    netinfo = {}
    for name in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni
    pad_net = {(r, p): n for n, conns in nets.items() for r, p in conns}

    # footprints
    for ref, (lib_id, value, fpid, extra) in COMPONENTS.items():
        fp = load_fp(fpid)
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPath(pcbnew.KIID_PATH(f"/{uid('sym-' + ref)}"))
        board.Add(fp)
        if ref == "U1":
            fp.SetPosition(V(*PICO_C))
            fp.Reference().SetVisible(False)       # covered by the module
        elif ref == "J1":
            fp.SetPosition(V(*NANO_C))
            fp.Flip(fp.GetPosition(), True)        # to bottom, mirror left/right
            fp.Reference().SetVisible(False)
        else:
            x, y, rot, _lbl = BOTTOM_PARTS[ref]
            fp.SetPosition(V(x, y))
            fp.SetOrientationDegrees(rot)
            fp.Flip(fp.GetPosition(), True)
            fp.Reference().SetVisible(False)
        if extra.get("DNP"):
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        for pad in fp.Pads():
            n = pad_net.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netinfo[n])

    # sanity check of the Nano header orientation (top view)
    j1 = board.FindFootprintByReference("J1")
    pads = {p.GetNumber(): p.GetPosition() for p in j1.Pads()}
    p1, p16 = pads["1"], pads["16"]
    assert pcbnew.ToMM(p1.x) > CX and pcbnew.ToMM(p1.y) > NANO_C[1], "J1 pin1 must be bottom-right"
    assert pcbnew.ToMM(p16.x) < CX and pcbnew.ToMM(p16.y) < NANO_C[1], "J1 pin16 must be top-left"
    u1 = board.FindFootprintByReference("U1")
    up = {p.GetNumber(): p.GetPosition() for p in u1.Pads()}
    assert pcbnew.ToMM(up["1"].x) < CX and pcbnew.ToMM(up["40"].x) > CX

    # outline (Pico W antenna notch at the far end)
    pts = board_outline_pts()
    for a, b in zip(pts, pts[1:] + pts[:1]):
        seg(board, a[0], a[1], b[0], b[1])

    # keep copper away from Pico W bottom-side test points / SWD pads (datasheet 2.2)
    px, py = PICO_C
    for i, (tx, ty) in enumerate([(-1.0, -24.3), (1.0, -24.3), (0.0, -21.0),
                                  (-2.5, -16.0), (-2.5, -13.5), (-2.5, -11.0)]):
        add_rule_area(board, rect_pts(px + tx, py + ty, 2.4, 2.4), pcbnew.F_Cu, f"KEEPOUT_TP{i + 1}")
    add_rule_area(board, rect_pts(px + 3.124, py + 5.7, 7.6, 2.6), pcbnew.F_Cu, "KEEPOUT_SWD")

    # silkscreen
    for ref, (x, y, rot, lbl) in BOTTOM_PARTS.items():
        if lbl:
            dx = 3.4 if ref.startswith("D") else 2.9
            add_text(board, lbl, x - dx, y, pcbnew.B_SilkS, 0.6, mirror=True)
    add_text(board, "PICO-ALVIK v1.5", CX, 120.6, pcbnew.B_SilkS, 0.7, rot=90, mirror=True)
    add_text(board, "USB", CX, BY0 + 2.0, pcbnew.B_SilkS, 0.8, mirror=True)

    pcbnew.SaveBoard(PCB, board)
    board = pcbnew.LoadBoard(PCB)
    ok = pcbnew.ExportSpecctraDSN(board, DSN)
    print("placed; DSN export:", ok)


# ---------------------------------------------------------------------------
# SES import (pcbnew.ImportSpecctraSES needs the GUI board, so parse it here)
# ---------------------------------------------------------------------------
def tokenize(s):
    return re.findall(r'"[^"]*"|\(|\)|[^\s()]+', s)


def parse_sexpr(tokens):
    stack = [[]]
    for t in tokens:
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(t.strip('"'))
    return stack[0][0]


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def import_ses(board):
    tree = parse_sexpr(tokenize(open(SES).read()))
    routes = find(tree, "routes")[0]
    res = find(routes, "resolution")[0]           # e.g. ["resolution", "um", "10"]
    unit = {"um": 0.001, "mm": 1.0, "mil": 0.0254, "inch": 25.4}[res[1]]
    scale = unit / float(res[2])                  # DSN units -> mm
    # via padstacks
    vias = {}
    lib = find(routes, "library_out")
    if lib:
        for ps in find(lib[0], "padstack"):
            m = re.search(r"_(\d+):(\d+)_um", ps[1])
            if m:
                vias[ps[1]] = (int(m.group(1)) / 1000.0, int(m.group(2)) / 1000.0)
    layer_map = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
    n_tr = n_via = 0
    for net in find(find(routes, "network_out")[0], "net"):
        ni = board.FindNet(net[1])
        for w in find(net, "wire"):
            path = find(w, "path")[0]
            layer, width = layer_map[path[1]], float(path[2]) * scale
            xy = [float(v) * scale for v in path[3:]]
            pts = [(xy[i], -xy[i + 1]) for i in range(0, len(xy), 2)]
            for a, b in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(V(*a))
                t.SetEnd(V(*b))
                t.SetWidth(mm(width))
                t.SetLayer(layer)
                t.SetNet(ni)
                board.Add(t)
                n_tr += 1
        for v in find(net, "via"):
            dia, drill = vias.get(v[1], (0.6, 0.3))
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(V(float(v[2]) * scale, -float(v[3]) * scale))
            via.SetWidth(mm(dia))
            via.SetDrill(mm(drill))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetNet(ni)
            board.Add(via)
            n_via += 1
    print(f"imported {n_tr} track segments, {n_via} vias")


def add_gnd_zone(board, layer, prio):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(board.FindNet("GND"))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(0.25))
    z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in board_outline_pts():
        ol.Append(V(x, y))
    board.Add(z)


GEOM = os.path.join(OUT, "geometry.json")
ROUTES = os.path.join(OUT, "routes.json")


def bbox_mm(item):
    b = item.GetBoundingBox()
    return [pcbnew.ToMM(b.GetLeft()), pcbnew.ToMM(b.GetTop()),
            pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom())]


def geom():
    """Export everything the grid router needs."""
    board = pcbnew.LoadBoard(PCB)
    cu = {pcbnew.F_Cu: "F", pcbnew.B_Cu: "B"}
    pads, shapes = [], []
    for fp in board.GetFootprints():
        fp_nets = sorted({p.GetNetname() for p in fp.Pads() if p.GetNetname()})
        for p in fp.Pads():
            pads.append({"ref": fp.GetReference(), "pin": p.GetNumber(),
                         "net": p.GetNetname(),
                         "layers": [n for l, n in cu.items() if p.IsOnLayer(l)],
                         "bbox": bbox_mm(p)})
        for g in fp.GraphicalItems():
            if g.GetLayer() in cu and g.GetClass() in ("FP_SHAPE", "PCB_SHAPE", "MGRAPHIC"):
                shapes.append({"ref": fp.GetReference(), "layer": cu[g.GetLayer()],
                               "nets": fp_nets, "bbox": bbox_mm(g)})
    keepouts = []
    for z in board.Zones():
        if z.GetIsRuleArea():
            ol = z.Outline().Outline(0)
            pts = [(pcbnew.ToMM(ol.CPoint(i).x), pcbnew.ToMM(ol.CPoint(i).y))
                   for i in range(ol.PointCount())]
            keepouts.append({"layers": [n for l, n in cu.items() if z.IsOnLayer(l)],
                             "pts": pts})
    nets = build_nets()
    data = {"outline": board_outline_pts(), "pads": pads, "shapes": shapes,
            "keepouts": keepouts,
            "nets": {n: {"pins": c, "power": n in POWER_NETS} for n, c in nets.items()}}
    with open(GEOM, "w") as f:
        json.dump(data, f, indent=1)
    print("geometry written:", GEOM)


def import_routes(board):
    data = json.load(open(ROUTES))
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
    print(f"imported {len(data['tracks'])} track segments, {len(data['vias'])} vias")


def finish():
    board = pcbnew.LoadBoard(PCB)
    for t in list(board.GetTracks()):
        board.Remove(t)
    for z in list(board.Zones()):
        if not z.GetIsRuleArea():
            board.Remove(z)
    if os.path.exists(ROUTES):
        import_routes(board)
    else:
        import_ses(board)
    add_gnd_zone(board, pcbnew.F_Cu, 0)
    add_gnd_zone(board, pcbnew.B_Cu, 0)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    rpt = os.path.join(OUT, "drc_report.txt")
    pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    print("finished; DRC report:", rpt)


if __name__ == "__main__":
    {"place": place, "geom": geom, "finish": finish}[sys.argv[1]]()
