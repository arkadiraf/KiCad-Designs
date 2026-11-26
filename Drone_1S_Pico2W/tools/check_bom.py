#!/usr/bin/python3
"""Check that every symbol and footprint in design.FRAME_BOM resolves (KD_* in the shared
Libraries folder, the rest in the stock KiCad libraries), and that every chip resistor and
capacitor on both boards follows the repository passives rule (README.md, "Design rules"):
resistors and capacitors 0603; bulk capacitors (>= 10 uF) 0805 or 1206. Prints BOM OK."""
import os
import re
import sys

import pcbnew

from design import FC, FRAME_BOM, SHARED_LIBS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.normpath(os.path.join(ROOT, SHARED_LIBS))
STOCK = "/usr/share/kicad"


def sym_ok(lib_id):
    lib, name = lib_id.split(":")
    path = os.path.join(SHARED if lib.startswith("KD_") else os.path.join(STOCK, "symbols"), f"{lib}.kicad_sym")
    return os.path.exists(path) and re.search(rf'\(symbol "{re.escape(name)}"', open(path).read()) is not None


def fp_ok(lib_id):
    lib, name = lib_id.split(":")
    base = SHARED if lib.startswith("KD_") else os.path.join(STOCK, "footprints")
    return pcbnew.FootprintLoad(os.path.join(base, f"{lib}.pretty"), name) is not None


def farads(val):
    m = re.match(r"\s*([\d.]+)\s*([pnu])", val)
    return float(m.group(1)) * {"p": 1e-12, "n": 1e-9, "u": 1e-6}[m.group(2)] if m else None


def passive_rule(refs, val, fp):
    """None if fine, else the reason. Only R_ / C_ chip footprints are checked."""
    m = re.match(r"(?:\w+:)?([RC])_(\d{4})_", fp)
    if not m:
        return None
    kind, size = m.groups()
    if kind == "R":
        return None if size == "0603" else f"resistor {size}, rule: 0603"
    f = farads(val)
    if f is not None and f >= 9.99e-6:          # 10 uF and up (float-safe)
        return None if size in ("0805", "1206") else f"bulk capacitor {val} in {size}, rule: 0805 / 1206"
    if f is None:
        return None if size in ("0603", "0805", "1206") else f"capacitor {size}, rule: 0603 (bulk 0805 / 1206)"
    return None if size == "0603" else f"capacitor {val} in {size}, rule: 0603"


bad, n = [], 0
for ref, lib, fpn, val, _pos, _rot in FC["sensors"]:
    why = passive_rule(ref, val, f"{lib}:{fpn}")
    if why:
        bad.append(f"FC {ref}: {why}")
for refs, val, sym, fp, role in FRAME_BOM:
    n += len(refs.split())
    if not sym_ok(sym):
        bad.append(f"{refs}: symbol {sym}")
    if not fp_ok(fp):
        bad.append(f"{refs}: footprint {fp}")
    why = passive_rule(refs, val, fp)
    if why:
        bad.append(f"{refs}: {why}")
print(f"{len(FRAME_BOM)} frame BOM lines, {n} parts + FC passives: {len(bad)} problems (unresolved / passives rule)")
for b in bad:
    print("  ", b)
print("BOM OK" if not bad else "BOM FAIL")
sys.exit(1 if bad else 0)
