#!/usr/bin/env python3
"""Check a Digi-Key cart export (xlsx) against the BOM for N boards.

    python verify_order.py ../fabrication/DigiKey_order_2026-11-27T074756.xlsx [boards=5]

Every orderable line (not stock, not DNP, not 'any' / pads) is matched by MPN. Lines bought elsewhere are listed
under OTHER_SOURCES. Prints OK / SHORT / MISSING per part and the cart lines that are not in the BOM.
"""
import sys

import openpyxl

from export_bom import is_stock, rows

OTHER_SOURCES = {           # MPN -> where it is ordered instead of Digi-Key
    "BM06B-SRSS-G-TB(LF)(SN)": "Mouser 306-6BSRSSGTBLPP",
    "4765": "4project 4P-537582 (Pololu cable)",
    "3072": "Pololu", "4761": "Pololu",
    "SC0919": "Mouser / Piitel (user, 2026-11-27)",
}
OTHER_PROJECT = {           # cart lines that belong to another board in this repo
    "6-146132-3": "Pico_Alvik_Adapter J1 (2 x 1x15 SMD male header per adapter)",
    "PMEG6020ER,115": "Pico_Alvik_Adapter D1",
}
ALTERNATIVES = {"SS12SDP4": "AS12AP"}     # alternative ordered in the same cart -> part it backs up


def cart(path):
    ws = openpyxl.load_workbook(path, data_only=True).active
    out = {}
    for r in ws.iter_rows(min_row=3, values_only=True):
        if r and r[2] and r[3]:
            out[str(r[3]).strip()] = (int(r[1]), str(r[2]).strip(), str(r[4] or ""))
    return out


def main():
    path = sys.argv[1]
    boards = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    c = cart(path)
    need = {}
    for refs, qty, val, fp, role, mfr, mpn, status, note in rows()[0]:
        if status == "DNP" or qty == 0 or is_stock(mpn) or mfr in ("any", "-"):
            continue
        need.setdefault(mpn, [0, []])
        need[mpn][0] += qty
        need[mpn][1].append(refs)
    print(f"Cart {path}: {len(c)} lines; BOM for {boards} boards\n")
    print(f"{'MPN':28} {'refs':22} {'need':>5} {'cart':>5}  result")
    used = set()
    bad = 0
    for mpn, (q, refs) in need.items():
        n = q * boards
        if mpn in OTHER_SOURCES:
            res, have = f"other source: {OTHER_SOURCES[mpn]}", "-"
        elif mpn in c:
            have = c[mpn][0]
            used.add(mpn)
            res = "OK" if have >= n else f"SHORT by {n - have}"
            bad += have < n
        else:
            have, res = 0, "MISSING"
            bad += 1
        print(f"{mpn[:28]:28} {' '.join(refs)[:22]:22} {n:>5} {str(have):>5}  {res}")
    extra = [m for m in c if m not in used]
    if extra:
        print("\nCart lines not in the BOM:")
        for m in extra:
            tag = (f"  (alternative to {ALTERNATIVES[m]})" if m in ALTERNATIVES else
                   f"  (other project: {OTHER_PROJECT[m]})" if m in OTHER_PROJECT else "  (NOT IN ANY BOM)")
            print(f"  {m}: {c[m][0]} x {c[m][1]} {c[m][2]}" + tag)
    print("\nORDER OK" if not bad else f"\nORDER INCOMPLETE: {bad} line(s) short or missing")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
