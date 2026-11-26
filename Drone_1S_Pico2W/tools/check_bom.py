#!/usr/bin/python3
"""Check that every symbol and footprint in design.FRAME_BOM resolves: KD_* in the shared
Libraries folder, the rest in the stock KiCad libraries. Prints BOM OK."""
import os
import re
import sys

import pcbnew

from design import FRAME_BOM, SHARED_LIBS

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


bad, n = [], 0
for refs, val, sym, fp, role in FRAME_BOM:
    n += len(refs.split())
    if not sym_ok(sym):
        bad.append(f"{refs}: symbol {sym}")
    if not fp_ok(fp):
        bad.append(f"{refs}: footprint {fp}")
print(f"{len(FRAME_BOM)} BOM lines, {n} parts, {len(bad)} unresolved")
for b in bad:
    print("  ", b)
print("BOM OK" if not bad else "BOM FAIL")
sys.exit(1 if bad else 0)
