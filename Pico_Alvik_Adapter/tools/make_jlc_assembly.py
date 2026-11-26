#!/usr/bin/env python3
"""JLCPCB assembly files from KiCad outputs.

usage: make_jlc_assembly.py <python-bom.xml> <kicad positions.csv> <JLC_BOM.csv> <JLC_CPL.csv>

BOM columns: Comment, Designator, Footprint, LCSC Part #   (LCSC numbers left blank:
fill them in on the JLC website or in LCSC below).
CPL columns: Designator, Mid X, Mid Y, Layer, Rotation      (from the KiCad pos file;
check rotations in JLC's placement preview, library zero-orientations differ).
U1 (Pico W module), J1 (two 1x15 headers in one footprint; JLC needs one part per
designator) and the solder jumpers are hand-fitted / not placed.
"""
import csv
import sys
import xml.etree.ElementTree as ET

LCSC = {}          # e.g. {"C1": "C15850"}  - verify on lcsc.com before use
NOT_PLACED = {"U1", "J1"}   # Pico module + the 2-row header footprint: hand-fitted

bom_xml, pos_csv, out_bom, out_cpl = sys.argv[1:5]
root = ET.parse(bom_xml).getroot()
groups = {}
for c in root.iter("comp"):
    ref = c.get("ref")
    if ref.startswith("#") or ref.startswith("JP") or ref in NOT_PLACED:
        continue
    key = (c.findtext("value"), c.findtext("footprint").split(":")[-1])
    groups.setdefault(key, []).append(ref)
with open(out_bom, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for (val, fp), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
        refs.sort()
        w.writerow([val, ",".join(refs), fp, LCSC.get(refs[0], "")])

placed = {r for refs in groups.values() for r in refs}
with open(pos_csv) as f, open(out_cpl, "w", newline="") as g:
    w = csv.writer(g)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for row in csv.DictReader(f):
        if row["Ref"] in placed:
            w.writerow([row["Ref"], f'{float(row["PosX"]):.4f}mm', f'{float(row["PosY"]):.4f}mm',
                        "Top" if row["Side"] == "top" else "Bottom", f'{float(row["Rot"]):.0f}'])
print("JLC assembly files written:", out_bom, out_cpl)
