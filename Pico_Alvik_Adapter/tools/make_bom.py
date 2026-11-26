#!/usr/bin/env python3
"""Grouped BOM CSV from KiCad's intermediate XML netlist (python-bom export)."""
import csv
import sys
import xml.etree.ElementTree as ET

NOTES = {
    "U1": "Raspberry Pi Pico W (SC0918), solder by castellated pads, no headers",
    "J1": "2x 1x15 2.54mm SMD male pin header, e.g. Samtec TSM-115-01-T-SV",
    "D1": "Schottky 2A/60V SOD-123W (Nexperia PMEG6020ER); VIN->VSYS",
    "D2": "Schottky 2A/60V SOD-123W (Nexperia PMEG6020ER); USB VBUS->VIN (Alvik charging)",
    "D3": "Schottky 2A/60V SOD-123W (Nexperia PMEG6020ER); USB VBUS->Nano VUSB pin",
    "JP4": "solder jumper, open by default (bypass D3)",
    "C1": "MLCC 10uF 10V X5R 0805",
    "JP1": "solder jumper, open by default (bypass D1)",
    "JP2": "solder jumper, bridged by default (cut to isolate)",
    "JP3": "solder jumper, open by default",
}

root = ET.parse(sys.argv[1]).getroot()
rows = {}
for c in root.iter("comp"):
    ref = c.get("ref")
    if ref.startswith("#"):
        continue
    val = c.findtext("value")
    fp = c.findtext("footprint")
    dnp = any(p.get("name") == "dnp" for p in c.iter("property")) or "DNP" in val
    key = (val, fp, dnp)
    rows.setdefault(key, []).append(ref)

with open(sys.argv[2], "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["References", "Qty", "Value", "Footprint", "Populate", "Notes"])
    for (val, fp, dnp), refs in sorted(rows.items(), key=lambda kv: kv[1][0]):
        refs.sort()
        w.writerow([" ".join(refs), len(refs), val, fp, "no" if dnp else "yes",
                    " | ".join(f"{r}: {NOTES[r]}" if len(refs) > 1 else NOTES[r] for r in refs if r in NOTES)])
print("BOM written:", sys.argv[2])
