#!/usr/bin/env python3
"""Generate the project-local footprint library ../Drone_1S.pretty and the
fp-lib-table of both boards.

Footprints
----------
* RPi_Pico_2_W_SMD_Castellated: Pico 2 W datasheet (RP-008304-DS-4), Figure 5
  (Materials/extracted/pico2w_smt_footprint.png). Its dimensions are identical
  to the Pico W figure used by Pico_Alvik_Adapter (pads 3.2 x 1.6 mm, 0.79 mm
  outside the module edge, rows 17.78 mm, footprint 22.58 mm wide, USB shell
  pads A-D, test points TP1-3, SWD pads E-G).
* CF_Deck_1x10_P2.00mm_SMD: one Crazyflie 2.x deck connector row, SMD.
  Geometry from Bitcraze crazyflie2-exp-template-electronics (c8f9a2e),
  ecad/libs/CF2-DECK-SMD-HOLES.kicad_mod, CC-BY 3.0, keeping only its SMD
  pads (1 x 1.6 mm, staggered +-1.6 mm, 2.0 mm pitch). The two rows sit
  22.0 mm apart (template P1 / P2).
"""

import os
from design import uid, LIB

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PRETTY = os.path.join(ROOT, f"{LIB}.pretty")


def line(x1, y1, x2, y2, layer, w):
    return (f'  (fp_line (start {x1:g} {y1:g}) (end {x2:g} {y2:g}) '
            f'(stroke (width {w:g}) (type solid)) (layer "{layer}") (tstamp {uid(f"l{x1}{y1}{x2}{y2}{layer}")}))')


def rect(x1, y1, x2, y2, layer, w):
    return (f'  (fp_rect (start {x1:g} {y1:g}) (end {x2:g} {y2:g}) '
            f'(stroke (width {w:g}) (type solid)) (fill none) (layer "{layer}") (tstamp {uid(f"r{x1}{y1}{x2}{y2}{layer}")}))')


def text(kind, val, x, y, layer, size=1.0, thick=0.15, ang=0, hide=False):
    h = " hide" if hide else ""
    return (f'  (fp_text {kind} "{val}" (at {x:g} {y:g} {ang}) (layer "{layer}"){h}\n'
            f'    (effects (font (size {size:g} {size:g}) (thickness {thick:g})))\n'
            f'    (tstamp {uid(f"t{kind}{val}{x}{y}{layer}")})\n  )')


def footprint(name, descr, tags, attr, graphics, pads):
    return (f'(footprint "{name}" (version 20221018) (generator pcbnew)\n  (layer "F.Cu")\n'
            f'  (descr "{descr}")\n  (tags "{tags}")\n  (attr {attr})\n'
            + "\n".join(graphics) + "\n" + "\n".join(pads) + "\n)\n")


# Pico 2 W test points / SWD pads on the module underside, in footprint
# coordinates (origin at module centre, USB at -Y, pin 1 at -X).
# Datasheet origin is the module's bottom-left corner: fx = x - 10.5, fy = 25.5 - y.
PICO_TP = [(8 - 10.5, 25.5 - y) for y in (41.5, 39.0, 36.5)]           # 1.5 x 1.5 mm
PICO_SWD = [(x - 10.5, 25.5 - 19.8) for x in (11.0841, 13.6241, 16.1641)]  # 1.5748 mm


def fp_pico():
    pads = []
    px = 9.69          # (22.58 - 3.2) / 2: pad centre from the module axis
    for p in range(1, 21):
        y = -24.13 + 2.54 * (p - 1)
        pads.append(f'  (pad "{p}" smd roundrect (at {-px:g} {y:g}) (size 3.2 1.6) '
                    f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.125) (solder_paste_margin 0.3) (tstamp {uid(f"pico{p}")}))')
    for p in range(21, 41):
        y = 24.13 - 2.54 * (p - 21)
        pads.append(f'  (pad "{p}" smd roundrect (at {px:g} {y:g}) (size 3.2 1.6) '
                    f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.125) (solder_paste_margin 0.3) (tstamp {uid(f"pico{p}")}))')
    # USB connector shell solder-relief pads A..D (no net, no paste), datasheet Fig. 5
    for n, (x, y, w, h) in enumerate([(-2.725, -24.0, 1.1, 1.8), (2.725, -24.0, 1.1, 1.8),
                                      (-2.425, -20.97, 1.05, 1.45), (2.425, -20.97, 1.05, 1.45)]):
        pads.append(f'  (pad "" smd roundrect (at {x:g} {y:g}) (size {w:g} {h:g}) '
                    f'(layers "F.Cu" "F.Mask") (roundrect_rratio 0.5) (tstamp {uid(f"picousb{n}")}))')
    g = [
        text("reference", "REF**", 0, -28.0, "F.SilkS"),
        text("value", "RPi_Pico_2_W", 0, 0, "F.Fab", ang=90),
        text("user", "${REFERENCE}", 0, -3, "F.Fab", ang=90),
        rect(-10.5, -25.5, 10.5, 25.5, "F.Fab", 0.1),          # module 21 x 51
        rect(-4.0, -26.8, 4.0, -21.5, "F.Fab", 0.1),           # micro USB, 1.3 mm overhang
        rect(-7.0, 16.5, 7.0, 25.5, "F.Fab", 0.1),             # antenna cut-out 14 x 9
        text("user", "ANTENNA 14x9 KEEP-OUT", 0, 21.0, "F.Fab", size=0.8, thick=0.12),
        text("user", "USB", 0, -19.0, "F.Fab", size=0.8, thick=0.12),
        line(-8.0, -25.3, -4.3, -25.3, "F.SilkS", 0.15),
        line(4.3, -25.3, 8.0, -25.3, "F.SilkS", 0.15),
        line(-10.3, 25.3, -7.6, 25.3, "F.SilkS", 0.15),
        line(7.6, 25.3, 10.3, 25.3, "F.SilkS", 0.15),
        line(-11.5, -25.3, -9.0, -25.3, "F.SilkS", 0.2),       # pin-1 marker
        rect(-11.55, -27.05, 11.55, 25.75, "F.CrtYd", 0.05),
    ]
    for i, (x, y) in enumerate(PICO_TP):
        g.append(rect(x - 0.75, y - 0.75, x + 0.75, y + 0.75, "F.Fab", 0.05))
        g.append(text("user", f"TP{i + 1}", x + 2.0, y, "F.Fab", size=0.5, thick=0.08))
    for i, (x, y) in enumerate(PICO_SWD):
        g.append(rect(x - 0.79, y - 0.79, x + 0.79, y + 0.79, "F.Fab", 0.05))
    g.append(text("user", "SWD", PICO_SWD[1][0], PICO_SWD[1][1] + 1.6, "F.Fab", size=0.5, thick=0.08))
    return footprint("RPi_Pico_2_W_SMD_Castellated",
                     "Raspberry Pi Pico 2 W, surface-mounted by its castellated pads. Pad geometry per Pico 2 W "
                     "datasheet Fig. 5. Keep top copper away from TP1-3, the SWD pads and the antenna area.",
                     "RPi Pico 2 W RP2350 castellated SMD module", "smd", g, pads)


def fp_deck():
    """Pin 1 at -X (as the Bitcraze footprint); odd pins at -1.6 Y, even at +1.6 Y."""
    pads = []
    for p in range(1, 11):
        x = -9 + 2 * (p - 1)
        y = -1.6 if p % 2 else 1.6
        pads.append(f'  (pad "{p}" smd rect (at {x:g} {y:g}) (size 1 1.6) '
                    f'(layers "F.Cu" "F.Paste" "F.Mask") (tstamp {uid(f"deck{p}")}))')
    g = [
        text("reference", "REF**", 0, -3.4, "F.SilkS"),
        text("value", "CF_Deck_1x10_P2.00mm_SMD", 0, 3.4, "F.Fab", size=0.8, thick=0.12),
        rect(-10.0, -1.0, 10.0, 1.0, "F.Fab", 0.1),             # connector body
        line(-10.6, -2.6, -10.6, 2.6, "F.SilkS", 0.15),         # pin-1 end
        text("user", "1", -11.4, -1.6, "F.SilkS", size=0.8, thick=0.15),
        rect(-11.0, -2.65, 11.0, 2.65, "F.CrtYd", 0.05),
    ]
    return footprint("CF_Deck_1x10_P2.00mm_SMD",
                     "Crazyflie 2.x deck connector row, 1x10 2.00 mm, SMD pads only. From Bitcraze "
                     "crazyflie2-exp-template-electronics CF2-DECK-SMD-HOLES (CC-BY 3.0). Rows 22.0 mm apart.",
                     "Crazyflie deck connector 2.00mm", "smd", g, pads)


def write_tables():
    for board in ("Frame", "FC"):
        with open(os.path.join(ROOT, board, "fp-lib-table"), "w") as f:
            f.write(f'(fp_lib_table\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/../{LIB}.pretty")'
                    f'(options "")(descr "Drone_1S_Pico2W project footprints (generated by tools/gen_libs.py)"))\n)\n')


if __name__ == "__main__":
    os.makedirs(PRETTY, exist_ok=True)
    for name, txt in (("RPi_Pico_2_W_SMD_Castellated", fp_pico()), ("CF_Deck_1x10_P2.00mm_SMD", fp_deck())):
        with open(os.path.join(PRETTY, f"{name}.kicad_mod"), "w") as f:
            f.write(txt)
        print("wrote", name)
    write_tables()
