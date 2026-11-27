#!/usr/bin/env python3
"""Stage 0 board: outline, mounting holes, placement guides. Run with KiCad's Python:

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
                    HOLES, PROJECT, REVISION, DATE, SHARED_LIBS, ZONES, BOLT_KEEPOUT_R, HOLDER_HOLES, CLAMP_HOLES, COVER_PILLAR, to_kicad)

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
    t.SetTextThickness(MM(0.15))
    board.Add(t)


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


def main():
    write_hole_fp()
    board = pcbnew.BOARD()
    board.GetDesignSettings().SetBoardThickness(MM(1.6))
    tb = board.GetTitleBlock()
    tb.SetTitle(PROJECT)
    tb.SetRevision(REVISION)
    tb.SetDate(DATE)
    tb.SetComment(0, "Stage 0: outline, holes, placement guides (KiCad-Designs/PicoBalancer)")
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
    for x, y, d in HOLDER_HOLES:                      # holder locating holes (guides until the holder footprint exists)
        c = pcbnew.PCB_SHAPE(board)
        c.SetShape(pcbnew.SHAPE_T_CIRCLE)
        c.SetCenter(pt(x, y))
        c.SetEnd(pt(x + d / 2, y))
        c.SetLayer(pcbnew.Dwgs_User)
        c.SetWidth(MM(0.05))
        board.Add(c)
    bw, bl = HOLDER["body"]
    for ref, (x, y) in BT_POS.items():
        rect(board, x - bw / 2, y - bl / 2, x + bw / 2, y + bl / 2, pcbnew.Dwgs_User)
        s = HOLDER["pad_span_min"] / 2
        rect(board, x - 3.2, y - s, x + 3.2, y - s + 7.3, pcbnew.Dwgs_User)       # pad zones (catalog minimum)
        rect(board, x - 3.2, y + s - 7.3, x + 3.2, y + s, pcbnew.Dwgs_User)
        text(board, f"{ref} 1042", x, y - 4, pcbnew.Dwgs_User, 1.2)
        text(board, "+ end down", x, y + 4, pcbnew.Dwgs_User, 1.0)
    cx, cy = HOLDER_CHANNEL["x"], HOLDER_CHANNEL["y"]
    rect(board, cx[0], cy[0], cx[1], cy[1], pcbnew.Dwgs_User, 0.05)
    text(board, "USB-C", 0, -97.0, pcbnew.Dwgs_User, 1.0)
    text(board, "charger", 0, -30, pcbnew.Dwgs_User, 1.0)
    for i, (x, y, d) in enumerate(CLAMP_HOLES):           # battery-clamp bolts (Fusion PCB body, user)
        hole(board, f"H{len(HOLES) + i + 1}", x, y)
    px0, py0, px1, py1 = COVER_PILLAR
    rect(board, px0, py0, px1, py1, pcbnew.Dwgs_User, 0.1)
    text(board, "cover pillar", 0, -71, pcbnew.Dwgs_User, 0.9)
    (ex0, ex1), (ey0, ey1) = ENCODER_ZONE
    for sx in (-1, 1):
        rect(board, sx * ex0, ey0, sx * ex1, ey1, pcbnew.Dwgs_User, 0.05)
    text(board, "encoder connectors (on motors)", 0, 108, pcbnew.Dwgs_User, 1.2)
    for name, (x0, y0, x1, y1) in ZONES.items():
        rect(board, x0, y0, x1, y1, pcbnew.Dwgs_User, 0.05)
        text(board, name, (x0 + x1) / 2, (y0 + y1) / 2, pcbnew.Dwgs_User, 1.0)
    text(board, f"{PROJECT} rev {REVISION}", 12, 72, pcbnew.F_SilkS, 1.2)
    board.Save(PCB)
    def table(name, libs, ext):
        rows = [f'  (lib (name "{n}")(type "KiCad")(uri "${{KIPRJMOD}}/../Libraries/{n}{ext}")(options "")(descr ""))'
                for n in libs]
        with open(os.path.join(ROOT, name), "w") as f:
            f.write("\n".join([f"({name.replace('-', '_')}", "  (version 7)"] + rows + [")"]) + "\n")
    table("fp-lib-table", ("KD_Mechanical", "KD_Power", "KD_Sensors", "KD_Modules", "KD_Connectors"), ".pretty")
    table("sym-lib-table", ("KD_Power", "KD_Sensors", "KD_Modules"), ".kicad_sym")
    if not os.path.exists(PRO):
        json.dump({"meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1}, "board": {}, "sheets": [],
                   "boards": [], "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []}},
                  open(PRO, "w"), indent=2)
    # check: every board hole matches a DXF circle (0.01 mm, same diameter), and the counts agree
    dx = dxf_circles()
    bad = [h_ for h_ in HOLES if not any(abs(h_[0] - x) < 0.01 and abs(h_[1] - y) < 0.01 and abs(d - HOLE_D) < 0.01
                                          for x, y, d in dx)]
    print(f"{len(HOLES)} holes, {len(dx)} DXF circles, outline {BOARD_W} x {BOARD_H}: "
          + ("IMPORT OK" if not bad and len(dx) == len(HOLES) else f"IMPORT FAIL {bad}"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
