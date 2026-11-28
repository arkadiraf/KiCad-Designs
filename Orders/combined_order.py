#!/usr/bin/env python3
"""Combined Digi-Key order for all the boards in this repository, checked against a Digi-Key cart export.

    python Orders/combined_order.py <cart.xlsx> [boards=5] [out_dir]

Needs (per board, from each project's own BOM export, regenerate those first):
    Drone_1S_Pico2W/fabrication/BOM_DigiKey.csv   frame + FC + Qwiic deck (tools/export_bom.py)
    PicoBalancer/fabrication/BOM_DigiKey.csv      (tools/export_bom.py)
    Pico_Alvik_Adapter                            from its BOM CSV (Digi-Key numbers in the notes, listed below)
Stock parts (0603 sample book, 0805 LEDs) are not in those CSVs; parts bought elsewhere are listed separately.
Each need is multiplied by `boards` and matched to the cart by Digi-Key PN (then by MPN). Writes
<out_dir>/Combined_DigiKey_order.xlsx: Combined (every PN: need per project, cart, status), Add to cart, Cart only,
Other sources. Cart lines above the need are normal (price breaks, spares) and are only marked EXTRA.
"""
import csv
import os
import re
import sys

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Pico_Alvik_Adapter keeps a plain parts list (fabrication/Pico_Alvik_Adapter_BOM.csv); its orderable lines:
ALVIK = [  # (qty per board, mfr, MPN, Digi-Key PN, refs, description, note)
    (2, "TE Connectivity", "6-146132-3", "A124546-ND", "J1", "1x15 2.54 mm SMD male header", "2 per adapter"),
    (1, "Nexperia", "PMEG6020ER,115", "1727-5217-1-ND", "D1", "Schottky 60 V 2 A SOD-123W", ""),
    (1, "Murata", "GRM21BR61E106KA73L", "490-5523-1-ND", "C1", "10 uF 0805",
     "BOM says 10uF 10V X5R 0805, any part: counted on the 25 V 0805 bought for the other boards"),
]
ALVIK_OTHER = [("Raspberry Pi Pico W (SC0918)", 1, "U1", "castellated, no headers - not a Digi-Key line in the cart")]

# Cart lines that are in no BOM of this repository, with what is known about them
CART_NOTES = {
    "SMM-110-02-S-S": "NOT NEEDED by the repo: the drone's B2B socket was this Samtec part before the Sullins "
                      "NPPN101BFLD-RC (also in the cart, S5902-10-ND) replaced it - remove unless wanted for something else",
}


def norm(mpn):
    return re.sub(r"\((LF|SN)\)", "", str(mpn)).split(",")[0].strip().upper()


def read_csv(path, project):
    out = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            out.append(dict(project=project, qty=int(r["Quantity"]), mfr=r["Manufacturer"],
                            mpn=r["Manufacturer Part Number"], dk=r["Digi-Key Part Number"].strip(),
                            refs=r["Customer Reference"], desc=r["Description"], status=r.get("Status", ""),
                            note=r.get("Note", "")))
    return out


def needs():
    rows = read_csv(os.path.join(ROOT, "Drone_1S_Pico2W", "fabrication", "BOM_DigiKey.csv"), "Drone_1S_Pico2W")
    rows += read_csv(os.path.join(ROOT, "PicoBalancer", "fabrication", "BOM_DigiKey.csv"), "PicoBalancer")
    for q, mfr, mpn, dk, refs, desc, note in ALVIK:
        rows.append(dict(project="Pico_Alvik_Adapter", qty=q, mfr=mfr, mpn=mpn, dk=dk, refs=refs, desc=desc,
                         status="ok", note=note))
    return rows


def read_cart(path):
    ws = openpyxl.load_workbook(path, data_only=True).active
    out = []
    for r in ws.iter_rows(min_row=3, values_only=True):
        if r and r[2] and r[3] and str(r[1]).strip().isdigit():
            out.append(dict(qty=int(r[1]), dk=str(r[2]).strip(), mpn=str(r[3]).strip(), desc=str(r[4] or ""),
                            avail=r[7], backorder=r[8], unit=r[9], total=r[10]))
    return out


def main():
    cart_path = sys.argv[1]
    boards = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    out_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(cart_path))
    projects = ["Drone_1S_Pico2W", "PicoBalancer", "Pico_Alvik_Adapter"]
    cart = read_cart(cart_path)
    by_dk = {c["dk"]: c for c in cart}
    by_mpn = {norm(c["mpn"]): c for c in cart}

    lines, other = {}, []                      # key -> combined line
    for r in needs():
        if not r["dk"] or "not Digi-Key" in r["note"]:          # no Digi-Key line, or bought elsewhere (BOM note)
            if r["qty"]:
                other.append((r["project"], r["refs"], r["qty"] * boards, r["mfr"], r["mpn"], r["desc"], r["note"]))
            continue
        c = by_dk.get(r["dk"]) or by_mpn.get(norm(r["mpn"]))
        key = c["dk"] if c else r["dk"]
        L = lines.setdefault(key, dict(dk=key, mpn=r["mpn"], mfr=r["mfr"], desc=r["desc"], cart=c,
                                       need={p: 0 for p in projects}, refs=[], dnp=True, notes=[]))
        L["need"][r["project"]] += r["qty"] * boards
        L["refs"].append(f"{r['project'].split('_')[0]}: {r['refs']}")
        L["dnp"] &= r["status"] == "DNP" or r["qty"] == 0
        if c and c["dk"] != r["dk"]:
            L["notes"].append(f"{r['project']} BOM lists {r['dk']} ({r['mpn']}); cart has {c['dk']}")
    for project, refs, q, note in [("Pico_Alvik_Adapter", r, q * boards, n) for (_d, q, r, n) in ALVIK_OTHER]:
        other.append((project, refs, q, "Raspberry Pi", "SC0918", "Raspberry Pi Pico W", note))

    used = {L["cart"]["dk"] for L in lines.values() if L["cart"]}
    wb = openpyxl.Workbook()
    hfont, hfill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="44546A")
    fill = {"OK": None, "EXTRA": "E2EFDA", "SHORT": "F8CBAD", "MISSING": "F8CBAD", "OPTIONAL": "EDEDED",
            "NOT IN BOM": "FFF2CC", "BACKORDER": "FCE4D6"}

    def sheet(ws, title, head, widths):
        ws.append([title])
        ws["A1"].font = Font(bold=True, size=12)
        ws.append([])
        ws.append(head)
        for c in ws[3]:
            c.font, c.fill = hfont, hfill
        for k, w in enumerate(widths):
            ws.column_dimensions[chr(65 + k)].width = w
        ws.freeze_panes = "A4"

    def paint(ws, status):
        f = fill.get(status.split()[0] if status else "OK")
        if f:
            for c in ws[ws.max_row]:
                c.fill = PatternFill("solid", fgColor=f)

    ws = wb.active
    ws.title = "Combined"
    sheet(ws, f"Combined Digi-Key order, {boards} of each board ({', '.join(projects)}) vs cart "
              f"{os.path.basename(cart_path)}",
          ["Digi-Key PN", "MPN", "Manufacturer", "Description", *[p.split("_")[0] + f" x{boards}" for p in projects],
           "Need", "Cart", "Difference", "Status", "Unit ILS", "Cart ILS", "Used on", "Note"],
          (26, 24, 18, 36, 9, 9, 9, 7, 7, 10, 16, 9, 10, 40, 60))
    counts = {}
    add = []
    for L in sorted(lines.values(), key=lambda x: x["dk"]):
        need = sum(L["need"].values())
        c = L["cart"]
        have = c["qty"] if c else 0
        if L["dnp"] and need == 0:
            status = "OPTIONAL (DNP)" + (" - in cart" if c else "")
        elif not c:
            status = "MISSING"
            add.append((L["dk"], need, L["mpn"], L["desc"], ", ".join(L["refs"])))
        elif have < need:
            status = f"SHORT {need - have}"
            add.append((L["dk"], need - have, L["mpn"], L["desc"], ", ".join(L["refs"])))
        elif have > need:
            status = f"EXTRA +{have - need}"
        else:
            status = "OK"
        if c and c.get("backorder"):
            status += f"; BACKORDER {c['backorder']} (available {c['avail']})"
        k = status.split(";")[0].split()[0]
        counts[k] = counts.get(k, 0) + 1
        ws.append([L["dk"], L["mpn"], L["mfr"], (c or L)["desc"], *[L["need"][p] or None for p in projects], need,
                   have if c else None, (have - need) if c else -need, status, c["unit"] if c else None,
                   c["total"] if c else None, "; ".join(L["refs"]), "; ".join(L["notes"])])
        paint(ws, status if not status.startswith("OK;") else "BACKORDER")
    for c in cart:
        if c["dk"] in used:
            continue
        note = CART_NOTES.get(c["mpn"], "not in any BOM of this repo (other needs - user)")
        counts["NOT"] = counts.get("NOT", 0) + 1
        ws.append([c["dk"], c["mpn"], "", c["desc"], None, None, None, 0, c["qty"], c["qty"], "NOT IN BOM",
                   c["unit"], c["total"], "", note])
        paint(ws, "NOT IN BOM")
    ws.append([])
    ws.append(["Cart total ILS", "", "", "", "", "", "", "", "", "", "", "", sum(float(c["total"] or 0) for c in cart)])
    ws[ws.max_row][0].font = ws[ws.max_row][12].font = Font(bold=True)

    wa = wb.create_sheet("Add to cart")
    sheet(wa, "Lines to add to the cart (missing or short for the boards above)",
          ["Digi-Key PN", "Quantity to add", "MPN", "Description", "Used on"], (28, 14, 26, 44, 50))
    for row in add:
        wa.append(list(row))

    wo = wb.create_sheet("Other sources")
    sheet(wo, "Bought elsewhere (no Digi-Key line): local suppliers, Pololu, Raspberry Pi resellers",
          ["Project", "Refs / use", f"Qty x{boards}", "Manufacturer", "MPN / part", "Description", "Note"],
          (18, 16, 10, 20, 24, 50, 60))
    for row in other:
        wo.append(list(row))
    for w in wb:
        for row in w.iter_rows(min_row=4):
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "Combined_DigiKey_order.xlsx")
    wb.save(out)
    print(f"{out}: {len(lines)} Digi-Key lines needed, cart {len(cart)} lines; {counts}")
    for row in add:
        print(f"  ADD {row[0]} x{row[1]}  {row[2]}  ({row[4]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
