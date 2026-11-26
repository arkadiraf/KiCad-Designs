#!/usr/bin/env python3
"""Generate Pico_Alvik_Adapter.kicad_sch (KiCad 7 format) from design.py."""

import os
import re
from design import (PROJECT, LIB, COMPONENTS, SIGNALS, NO_CONNECT, build_nets, uid)

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
KICAD_SYM = "/usr/share/kicad/symbols"
ROOT = uid("root-sheet")
G = 1.27  # grid


# ---------------------------------------------------------------------------
# Library symbol helpers
# ---------------------------------------------------------------------------
def extract_symbol(lib_file, name):
    txt = open(lib_file).read()
    start = txt.index(f'(symbol "{name}"')
    depth = 0
    for i in range(start, len(txt)):
        if txt[i] == "(":
            depth += 1
        elif txt[i] == ")":
            depth -= 1
            if depth == 0:
                return txt[start:i + 1]
    raise ValueError(name)


def lib_symbol_text(lib_id):
    lib, name = lib_id.split(":")
    path = (os.path.join(PRJ, f"{LIB}.kicad_sym") if lib == LIB
            else os.path.join(KICAD_SYM, f"{lib}.kicad_sym"))
    body = extract_symbol(path, name)
    # rename the top-level symbol to "lib:name" (sub-units keep their names)
    return body.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)


PIN_RE = re.compile(r'\(pin (\w+) \w+ \(at ([-\d.]+) ([-\d.]+) (\d+)\).*?\(number "([^"]*)"', re.S)


def lib_pins(lib_id):
    """pin number -> (x, y, angle) in symbol (y-up) coordinates."""
    return {m.group(5): (float(m.group(2)), float(m.group(3)), int(m.group(4)))
            for m in PIN_RE.finditer(lib_symbol_text(lib_id))}


# ---------------------------------------------------------------------------
# Schematic item builders
# ---------------------------------------------------------------------------
items = []
lib_ids = set()
pwr_count = [0]


def fmt(v):
    return f"{round(v, 4):g}"


def pin_world(sx, sy, rot, px, py, pang):
    """Symbol pin -> schematic coordinates (y-down) and outward direction."""
    if rot == 0:
        x, y, a = px, py, pang
    elif rot == 180:
        x, y, a = -px, -py, (pang + 180) % 360
    elif rot == 90:
        x, y, a = -py, px, (pang + 90) % 360
    else:  # 270
        x, y, a = py, -px, (pang + 270) % 360
    wx, wy = sx + x, sy - y
    # pin angle points from the connection point into the body; outward is opposite
    out = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[a]
    return wx, wy, out


def place_symbol(ref, lib_id, value, footprint, x, y, rot=0, dnp=False,
                 ref_off=(0, -3), val_off=(0, 3), hide_ref=False, extra_props=()):
    lib_ids.add(lib_id)
    pins = lib_pins(lib_id)
    u = uid(f"sym-{ref}")
    hide = " hide" if hide_ref else ""
    props = [
        f'    (property "Reference" "{ref}" (at {fmt(x + ref_off[0])} {fmt(y + ref_off[1])} 0)\n'
        f'      (effects (font (size 1.27 1.27)){hide})\n    )',
        f'    (property "Value" "{value}" (at {fmt(x + val_off[0])} {fmt(y + val_off[1])} 0)\n'
        f'      (effects (font (size 1.27 1.27)))\n    )',
        f'    (property "Footprint" "{footprint}" (at {fmt(x)} {fmt(y)} 0)\n'
        f'      (effects (font (size 1.27 1.27)) hide)\n    )',
        f'    (property "Datasheet" "~" (at {fmt(x)} {fmt(y)} 0)\n'
        f'      (effects (font (size 1.27 1.27)) hide)\n    )',
    ]
    for k, v in extra_props:
        props.append(f'    (property "{k}" "{v}" (at {fmt(x)} {fmt(y)} 0)\n'
                     f'      (effects (font (size 1.27 1.27)) hide)\n    )')
    pin_lines = "\n".join(f'    (pin "{n}" (uuid {uid(f"pin-{ref}-{n}")}))' for n in pins)
    in_bom = "no" if ref.startswith("#") else "yes"
    items.append(
        f'  (symbol (lib_id "{lib_id}") (at {fmt(x)} {fmt(y)} {rot}) (unit 1)\n'
        f'    (in_bom {in_bom}) (on_board {"no" if ref.startswith("#") else "yes"}) (dnp {"yes" if dnp else "no"})\n'
        f'    (uuid {u})\n' + "\n".join(props) + "\n" + pin_lines + "\n"
        f'    (instances\n      (project "{PROJECT}"\n'
        f'        (path "/{ROOT}" (reference "{ref}") (unit 1))\n      )\n    )\n  )')
    return {n: pin_world(x, y, rot, *p) for n, p in pins.items()}


def wire(x1, y1, x2, y2):
    items.append(f'  (wire (pts (xy {fmt(x1)} {fmt(y1)}) (xy {fmt(x2)} {fmt(y2)}))\n'
                 f'    (stroke (width 0) (type default))\n    (uuid {uid(f"w{x1},{y1},{x2},{y2}")})\n  )')


def label(name, x, y, out):
    ang = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[out]
    just = "right" if ang in (180, 270) else "left"
    items.append(f'  (label "{name}" (at {fmt(x)} {fmt(y)} {ang}) (fields_autoplaced)\n'
                 f'    (effects (font (size 1.27 1.27)) (justify {just} bottom))\n'
                 f'    (uuid {uid(f"lbl{name}{x},{y}")})\n  )')


def no_connect(x, y):
    items.append(f'  (no_connect (at {fmt(x)} {fmt(y)}) (uuid {uid(f"nc{x},{y}")}))')


def gnd(x, y, rot=0):
    pwr_count[0] += 1
    off = {0: (0, 3.81), 90: (3.81, 0), 270: (-3.81, 0), 180: (0, -3.81)}[rot]
    place_symbol(f"#PWR0{pwr_count[0]:02d}", "power:GND", "GND", "", x, y, rot,
                 ref_off=(0, 6.35), val_off=off, hide_ref=True)


def pwr_flag(x, y, net):
    pwr_count[0] += 1
    place_symbol(f"#FLG0{pwr_count[0]:02d}", "power:PWR_FLAG", "PWR_FLAG", "", x, y,
                 ref_off=(0, -1.905), val_off=(0, -3.81), hide_ref=True)
    wire(x, y, x, y + 2.54)
    label(net, x, y + 2.54, (0, 1))


def note(txt, x, y, size=1.27):
    t = txt.replace('"', "'").replace("\n", "\\n")
    items.append(f'  (text "{t}" (at {fmt(x)} {fmt(y)} 0)\n'
                 f'    (effects (font (size {size:g} {size:g})) (justify left top))\n'
                 f'    (uuid {uid("note" + txt[:40])})\n  )')


# ---------------------------------------------------------------------------
# Build the sheet
# ---------------------------------------------------------------------------
def pin_net_map():
    m = {}
    for net, conns in build_nets().items():
        for ref, p in conns:
            m[(ref, p)] = net
    return m


def connect_pins(ref, pins, netmap, stub=2.54):
    for n, (x, y, out) in pins.items():
        net = netmap.get((ref, n))
        if net is None:
            if int(n) in NO_CONNECT.get(ref, []):
                no_connect(x, y)
            continue
        ex, ey = x + out[0] * stub, y + out[1] * stub
        wire(x, y, ex, ey)
        if net == "GND":
            # GND symbol body points away from the part
            gnd(ex, ey, {(1, 0): 90, (-1, 0): 270, (0, 1): 0, (0, -1): 180}[out])
        else:
            label(net, ex, ey, out)


def build():
    netmap = pin_net_map()

    # Main parts
    lid, val, fp, _ = COMPONENTS["U1"]
    u1 = place_symbol("U1", lid, val, fp, 76.2, 96.52, ref_off=(0, -29.21), val_off=(0, 29.21))
    connect_pins("U1", u1, netmap)

    lid, val, fp, _ = COMPONENTS["J1"]
    j1 = place_symbol("J1", lid, val, fp, 177.8, 91.44, ref_off=(0, -22.86), val_off=(0, 22.86))
    connect_pins("J1", j1, netmap)

    # Power / options section (bottom of the sheet)
    y1, y2 = 152.4, 175.26
    for ref, x, y, rot in (("D2", 50.8, y1, 180), ("D1", 88.9, y1, 180),
                           ("JP1", 88.9, y1 + 10.16, 0),
                           ("JP2", 50.8, y2, 0), ("JP3", 88.9, y2, 0)):
        lid, val, fp, ex = COMPONENTS[ref]
        dnp = ex.get("DNP", False)
        p = place_symbol(ref, lid, val, fp, x, y, rot, dnp=dnp, ref_off=(0, -3.3), val_off=(0, 3.3))
        connect_pins(ref, p, netmap)
    lid, val, fp, _ = COMPONENTS["C1"]
    c1 = place_symbol("C1", lid, val, fp, 116.84, y1 + 2.54, ref_off=(3.5, -1.3), val_off=(3.5, 1.3))
    connect_pins("C1", c1, netmap)

    # Power flags (power is delivered from off-board: Alvik VIN / Pico USB)
    pwr_flag(127.0, y2 - 5.08, "VIN")
    pwr_flag(137.16, y2 - 5.08, "VSYS")
    pwr_count[0] += 1
    place_symbol(f"#FLG0{pwr_count[0]:02d}", "power:PWR_FLAG", "PWR_FLAG", "", 147.32, y2 - 5.08,
                 ref_off=(0, -1.905), val_off=(0, -3.81), hide_ref=True)
    wire(147.32, y2 - 5.08, 147.32, y2 - 2.54)
    gnd(147.32, y2 - 2.54)

    # ----- notes ------------------------------------------------------------
    note("Pico W  ->  Arduino Alvik adapter (replaces the Nano ESP32)", 25.4, 22.86, 2.0)
    note("Pico W is reflow/hand soldered by its castellated pads on TOP.\n"
         "Nano-footprint 2x15 SMD male headers on BOTTOM plug into the Alvik.\n"
         "Net names = Nano pin name + Alvik function.", 25.4, 30.48)

    rows = ["Nano pin -> Pico GPIO   (Alvik use)"]
    for name, npin, ppin, gp, c in SIGNALS:
        nano = name.split("_")[0]
        rows.append(f"{nano:>4} (J1.{npin:<2}) -> {gp:<5} (U1.{ppin:<2})  {c}")
    note("\n".join(rows), 210.82, 30.48, 1.0)

    note("POWER  (diode-OR, no supply can back-feed another)\n"
         "USB plugged:   Pico VBUS -> on-board Schottky -> VSYS        (powers the Pico)\n"
         "               Pico VBUS -> D2 -> Nano VIN                  (charges/powers the Alvik,\n"
         "                                    same as Nano ESP32 VUSB->PMEG6020->VIN)\n"
         "USB unplugged: Alvik -> Nano VIN -> D1 -> VSYS             (Alvik powers the Pico)\n"
         "D2 also keeps Alvik power off the USB host; D1 keeps USB/VSYS off VIN except via D2.\n"
         "JP1 (open): bypass D1.   VSYS 1.8-5.5 V.\n"
         "JP2 (bridged): Pico 3V3(OUT) -> Nano 3V3 pin = Alvik +3V3_EXT (an OUTPUT of the\n"
         "controller; the Alvik powers the controller only via VIN). Pico 3V3 load < 300 mA.\n"
         "JP3 (open): Nano RST -> Pico RUN.  Nano VUSB/B0/B1, D8-D12: not connected.",
         160.02, 142.24, 1.0)


def write():
    build()
    libsyms = "\n".join(lib_symbol_text(l) for l in sorted(lib_ids))
    libsyms = "\n".join("    " + ln for ln in libsyms.splitlines())
    sch = f'''(kicad_sch (version 20230121) (generator eeschema)

  (uuid {ROOT})

  (paper "A4")

  (title_block
    (title "Pico Alvik Adapter")
    (date "2026-11-26")
    (rev "1.1")
    (company "KiCad-Designs")
    (comment 1 "Raspberry Pi Pico W carrier in Arduino Nano form factor for the Arduino Alvik robot")
    (comment 2 "Generated by tools/gen_schematic.py from tools/design.py")
  )

  (lib_symbols
{libsyms}
  )

{chr(10).join(items)}

  (sheet_instances
    (path "/" (page "1"))
  )
)
'''
    with open(os.path.join(PRJ, f"{PROJECT}.kicad_sch"), "w") as f:
        f.write(sch)
    print("schematic written")


if __name__ == "__main__":
    write()
