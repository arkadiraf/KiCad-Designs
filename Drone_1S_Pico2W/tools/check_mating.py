#!/usr/bin/python3
"""Check that the FC module mates with the frame: the FC's J1/J2 header pins
sit exactly under the frame's J5/J6 socket pins (same pin numbers, same plan
position along the row), and the four M2.5 holes line up. Both boards share
the same sheet origin (design.ORIGIN), so plan positions compare directly."""
import os, sys
import pcbnew
from design import FC, FRAME

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
fr = pcbnew.LoadBoard(os.path.join(ROOT, "Frame", FRAME["project"] + ".kicad_pcb"))
fc = pcbnew.LoadBoard(os.path.join(ROOT, "FC", FC["project"] + ".kicad_pcb"))
mm = pcbnew.ToMM


def pads(board, ref):
    fp = board.FindFootprintByReference(ref)
    return {p.GetNumber(): (mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in fp.Pads()}


ok = True
for h, s in (("J1", "J5"), ("J2", "J6")):
    a, b = pads(fc, h), pads(fr, s)
    row_y = {round(v[1], 3) for v in a.values()}
    for n in a:
        dx = abs(a[n][0] - b[n][0])
        dy = abs(a[n][1] - b[n][1])          # SMD socket pads are offset 1.6 mm from the pin line
        if dx > 0.01 or abs(dy - 1.6) > 0.01:
            ok = False
            print(f"MISMATCH FC {h}.{n} {a[n]} vs frame {s}.{n} {b[n]}")
    print(f"FC {h} <-> frame {s}: 10 pins, pin line y = {row_y}")
holes = lambda b, pre: sorted((round(mm(f.GetPosition().x), 3), round(mm(f.GetPosition().y), 3))
                              for f in b.GetFootprints() if f.GetReference().startswith(pre))
hf, hc = holes(fr, "H_CV"), holes(fc, "H")      # the shared cover / gear / standoff holes
print("M2 holes frame", hf, "\n         FC   ", hc)
ok &= hf == hc
print("MATING OK" if ok else "MATING FAILED")
sys.exit(0 if ok else 1)
