#!/usr/bin/python3
"""Check that every drilled hole in the frame board matches the OpenSCAD DXF
(position within 0.01 mm, same diameter) and that the outline matches."""
import math, os, sys
import pcbnew
import dxf_import
from design import to_kicad, FRAME

HERE = os.path.dirname(os.path.abspath(__file__))
board = pcbnew.LoadBoard(os.path.join(HERE, "..", "Frame", FRAME["project"] + ".kicad_pcb"))
outline, holes = dxf_import.load()
DXF_REFS = ("J1", "J2", "J3", "J4", "J8")     # + all H* holes: mounting / motor holes, ESC pins, JST-PH holes
drills = [(pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y), pcbnew.ToMM(p.GetDrillSize().x))
          for fp in board.GetFootprints() if fp.GetReference().startswith("H") or fp.GetReference() in DXF_REFS
          for p in fp.Pads() if p.GetDrillSize().x > 0]
bad, used = 0, set()
for h in holes:
    kx, ky = to_kicad(h["x"], h["y"])
    m = [i for i, (x, y, d) in enumerate(drills) if math.hypot(x - kx, y - ky) < 0.01 and abs(d - h["d"]) < 1e-3]
    if len(m) != 1:
        bad += 1
        print("missing", h)
    used.update(m)
extra = len(drills) - len(used)
edges = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
bb = board.GetBoardEdgesBoundingBox()
from gen_pcb import frame_outline_pts                # DXF outline + the rear USB tab
full = frame_outline_pts()
xs = [p[0] for p in full]
ok = bad == 0 and extra == 0 and len(edges) == len(full) and abs(pcbnew.ToMM(bb.GetWidth()) - 0.1 - (max(xs) - min(xs))) < 0.01
print(f"{len(used)} holes match the DXF, {bad} missing, {extra} extra; {len(edges)} outline segments for "
      f"{len(full)} vertices (DXF {len(outline)} + rear USB tab) -> {'IMPORT OK' if ok else 'IMPORT FAILED'}")
sys.exit(0 if ok else 1)
