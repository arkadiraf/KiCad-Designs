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
* Bosch_LGA-16_3x4.5mm_P0.5mm (BMI088): body 4.5 x 3.0 mm, 1.0 mm high (Bosch STEP
  model, via bit-bots/bitbots_imu_dxl). Pads 0.35 x 0.59 mm, 7 per long side at
  y = +-1.165, 1 per short side at x = +-1.915: identical in ArduPilot/Schematics
  (HKUST NxtPX4v2) and bit-bots; a third copy (Bosch_LGA-16_3x4.5mm_P0.5mm, cites
  BST-BMI088-DS000-19) has the same centres with smaller pads. Pin 1 at (-1.5, -1.165):
  1-7 along the -y edge towards +x, 8 at +x, 9-15 along +y back towards -x, 16 at -x, as
  ArduPilot / bit-bots. Check pin 1 against the Bosch datasheet before routing.
  Pin functions as the Crazyflie Bolt 1.1 schematic (Bitcraze, CC-BY-NC-SA 4.0).
* Bosch_LGA-10_2x2mm_P0.5mm (BMP388): body 2.0 x 2.0 mm, 0.75 mm high (STEP model,
  atopile/packages, LCSC). Pads 0.25 x 0.275 mm at +-0.7625 (OpenAXES; same pad centres
  as the KiCad generator footprint made from BST-BMP388-DS001), pin numbering as OpenAXES
  and the LCSC part: 1-2 on the -y side, 3-5 on -x, 6-7 on +y, 8-10 on +x.
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
PICO_TP = [(8 - 10.5, 25.5 - y) for y in (41.5, 39.0, 36.5)]           # 1.5 x 1.5 mm, 0.3 mm corner radius
# Datasheet 2.1: TP1 = GND, TP2 = USB DM, TP3 = USB DP, "can be used to access USB signals instead of
# the micro-USB port". Taken here in Fig. 5's order from the USB end (41.5, 39, 36.5) - TO CHECK
# against the Pico 2 W bottom silkscreen before routing.
PICO_TP_NAMES = ["TP1", "TP2", "TP3"]
PICO_SWD = [(x - 10.5, 25.5 - 19.8) for x in (11.0841, 13.6241, 16.1641)]  # 1.5748 mm (E square, F/G round)
# The 3-pin SWD debug port as SMT pads (datasheet 3.9: SWCLK, GND, SWDIO). Order E, F, G = SWCLK,
# GND, SWDIO assumed - TO CHECK against the Pico 2 W bottom silkscreen before routing.
PICO_SWD_NAMES = ["SWCLK", "SWD_GND", "SWDIO"]


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
    # TP1-TP3 (GND, USB DM, USB DP) as solder pads, to bring USB to J3 on the FC bottom
    for name, (x, y) in zip(PICO_TP_NAMES, PICO_TP):
        pads.append(f'  (pad "{name}" smd roundrect (at {x:g} {y:g}) (size 1.5 1.5) '
                    f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (tstamp {uid(f"picotp{name}")}))')
    # SWD pads E/F/G as solder pads, to bring SWD to the frame (J9) for recovery from the Pi
    for name, (x, y), shape in zip(PICO_SWD_NAMES, PICO_SWD, ("rect", "circle", "circle")):
        pads.append(f'  (pad "{name}" smd {shape} (at {x:g} {y:g}) (size 1.5748 1.5748) '
                    f'(layers "F.Cu" "F.Paste" "F.Mask") (tstamp {uid(f"picoswd{name}")}))')
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


def fp_bmi088():
    pads = []
    pos = [(-1.5 + 0.5 * k, -1.165) for k in range(7)] + [(1.915, 0.0)] + \
          [(1.5 - 0.5 * k, 1.165) for k in range(7)] + [(-1.915, 0.0)]
    for n, (x, y) in enumerate(pos, 1):
        w, h = (0.59, 0.35) if n in (8, 16) else (0.35, 0.59)
        pads.append(f'  (pad "{n}" smd rect (at {x:g} {y:g}) (size {w:g} {h:g}) '
                    f'(layers "F.Cu" "F.Paste" "F.Mask") (tstamp {uid(f"bmi{n}")}))')
    g = [text("reference", "REF**", 0, -2.4, "F.SilkS", size=0.6, thick=0.1),
         text("value", "BMI088", 0, 2.4, "F.Fab", size=0.5, thick=0.08),
         rect(-2.25, -1.5, 2.25, 1.5, "F.Fab", 0.1),
         line(-2.25, -1.0, -1.75, -1.5, "F.Fab", 0.1),                 # pin-1 corner
         line(-2.45, -1.7, -1.8, -1.7, "F.SilkS", 0.15),
         rect(-2.6, -1.85, 2.6, 1.85, "F.CrtYd", 0.05)]
    return footprint("Bosch_LGA-16_3x4.5mm_P0.5mm", "Bosch BMI088 LGA-16, 4.5 x 3.0 x 1.0 mm, 0.5 mm pitch "
                     "(pads as ArduPilot NxtPX4v2 / bit-bots; see gen_libs.py)", "Bosch BMI088 IMU LGA", "smd", g, pads)


def fp_bmp388():
    pads = []
    pos = [(0.25, -0.7625), (-0.25, -0.7625), (-0.7625, -0.5), (-0.7625, 0.0), (-0.7625, 0.5),
           (-0.25, 0.7625), (0.25, 0.7625), (0.7625, 0.5), (0.7625, 0.0), (0.7625, -0.5)]
    for n, (x, y) in enumerate(pos, 1):
        w, h = (0.25, 0.275) if abs(y) > 0.7 else (0.275, 0.25)
        pads.append(f'  (pad "{n}" smd rect (at {x:g} {y:g}) (size {w:g} {h:g}) '
                    f'(layers "F.Cu" "F.Paste" "F.Mask") (tstamp {uid(f"bmp{n}")}))')
    g = [text("reference", "REF**", 0, -1.7, "F.SilkS", size=0.6, thick=0.1),
         text("value", "BMP388", 0, 1.7, "F.Fab", size=0.5, thick=0.08),
         rect(-1.0, -1.0, 1.0, 1.0, "F.Fab", 0.1),
         line(0.5, -1.0, 1.0, -0.5, "F.Fab", 0.1),                     # pin-1 corner
         line(0.6, -1.25, 1.2, -1.25, "F.SilkS", 0.15),
         rect(-1.25, -1.25, 1.25, 1.25, "F.CrtYd", 0.05)]
    return footprint("Bosch_LGA-10_2x2mm_P0.5mm", "Bosch BMP388 LGA-10, 2.0 x 2.0 x 0.75 mm, 0.5 mm pitch "
                     "(pads as OpenAXES / KiCad generator from BST-BMP388-DS001; see gen_libs.py)",
                     "Bosch BMP388 barometer LGA", "smd", g, pads)


def fp_bitcraze_female():
    """Bitcraze female deck connector, PCB layout from its datasheet drawing (bitcraze/hardware
    female-deck-connector): pads 0.89 x 2.0 mm, 2.00 mm pitch, staggered, 5.4 mm overall
    (pad centres +-1.7 mm off the pin line). Body 20.5 x 2.0 x 2.1 mm. Pin 1 at -X like the
    KiCad PinSocket_..._SMD_Pin1Left; odd pads at -1.7 Y."""
    pads = []
    for p in range(1, 11):
        x = -9 + 2 * (p - 1)
        y = -1.7 if p % 2 else 1.7
        pads.append(f'  (pad "{p}" smd rect (at {x:g} {y:g}) (size 0.89 2) '
                    f'(layers "F.Cu" "F.Paste" "F.Mask") (tstamp {uid(f"bcf{p}")}))')
    g = [text("reference", "REF**", 0, -3.6, "F.SilkS", size=0.8, thick=0.12),
         text("value", "Bitcraze female deck connector", 0, 3.6, "F.Fab", size=0.6, thick=0.1),
         rect(-10.25, -1.0, 10.25, 1.0, "F.Fab", 0.1),
         line(-10.7, -2.9, -10.7, 2.9, "F.SilkS", 0.15),
         rect(-10.75, -2.95, 10.75, 2.95, "F.CrtYd", 0.05)]
    return footprint("Bitcraze_FemaleDeck_1x10_P2.00mm_SMD",
                     "Bitcraze female deck connector, 1x10 2.00 mm, SMD, 2.1 mm high (Bitcraze datasheet drawing)",
                     "Bitcraze Crazyflie deck female socket 2.00mm", "smd", g, pads)


def fp_usb_prog():
    """J3, USB programming pads on the FC bottom (DNP): 4 SMD pads 1.5 x 3.0 mm, 2.54 mm pitch,
    USB order VBUS, D-, D+, GND, for soldered wires or a 2.54 mm SMD right-angle header."""
    names = ["VBUS", "D-", "D+", "GND"]
    pads, g = [], []
    for n in range(4):
        x = -3.81 + 2.54 * n
        pads.append(f'  (pad "{n + 1}" smd roundrect (at {x:g} 0) (size 1.5 3) '
                    f'(layers "F.Cu" "F.Mask") (roundrect_rratio 0.15) (tstamp {uid(f"usbp{n}")}))')
        g.append(text("user", names[n], x, -3.6, "F.SilkS", size=0.6, thick=0.12, ang=90))
    g += [text("reference", "REF**", -6.2, 0, "F.SilkS", size=0.8, thick=0.12, ang=90),
          text("value", "USB_PROG_DNP", 0, 2.6, "F.Fab", size=0.6, thick=0.1),
          text("user", "USB DNP", 0, 2.4, "F.SilkS", size=0.7, thick=0.12),
          rect(-5.3, -5.1, 5.3, 1.75, "F.CrtYd", 0.05)]
    return footprint("USB_Prog_Pads_1x4_P2.54mm_SMD",
                     "USB programming pads (not populated): VBUS, D-, D+, GND, 2.54 mm, SMD",
                     "USB programming DNP pads", "smd exclude_from_bom", g, pads)


def write_tables():
    for board in ("Frame", "FC"):
        with open(os.path.join(ROOT, board, "fp-lib-table"), "w") as f:
            f.write(f'(fp_lib_table\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/../{LIB}.pretty")'
                    f'(options "")(descr "Drone_1S_Pico2W project footprints (generated by tools/gen_libs.py)"))\n)\n')


if __name__ == "__main__":
    os.makedirs(PRETTY, exist_ok=True)
    for name, txt in (("RPi_Pico_2_W_SMD_Castellated", fp_pico()), ("CF_Deck_1x10_P2.00mm_SMD", fp_deck()),
                      ("Bosch_LGA-16_3x4.5mm_P0.5mm", fp_bmi088()), ("Bosch_LGA-10_2x2mm_P0.5mm", fp_bmp388()),
                      ("Bitcraze_FemaleDeck_1x10_P2.00mm_SMD", fp_bitcraze_female()),
                      ("USB_Prog_Pads_1x4_P2.54mm_SMD", fp_usb_prog())):
        with open(os.path.join(PRETTY, f"{name}.kicad_mod"), "w") as f:
            f.write(txt)
        print("wrote", name)
    write_tables()
