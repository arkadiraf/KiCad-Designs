#!/usr/bin/env python3
"""Generate the shared KiCad libraries of this repository (KiCad 7 format, opens in 8/9).

    cd Libraries/tools && python3 gen_lib.py

Output (next to this tools/ folder):

    KD_Power.kicad_sym       BQ25606, TPS22997, TPS22810DBV, TPS61235P
    KD_Sensors.kicad_sym     BMI088, BMP388
    KD_Modules.kicad_sym     RPi_Pico_2_W
    KD_Power.pretty/         Texas_RYZ0010A_WQFN-HR-10_2x1.5mm_P0.5mm,
                             Texas_RWL_VQFN-HR-9_2.5x2.5mm_P0.5mm
    KD_Sensors.pretty/       Bosch_LGA-16_3x4.5mm_P0.5mm, Bosch_LGA-10_2x2mm_P0.5mm
    KD_Modules.pretty/       RPi_Pico_2_W_SMD_Castellated
    KD_Connectors.pretty/    Bitcraze_FemaleDeck_1x10_P2.00mm_SMD

Where KiCad's stock library already has a correct footprint, the symbol points at it
(BQ25606: Package_DFN_QFN:Texas_RGE0024H..., TPS22810DBV: Package_TO_SOT_SMD:SOT-23-6).

Every pinout and land pattern was cross-checked against at least two independent
open-source KiCad libraries (and a third where one existed). The TI and Bosch datasheets
could not be downloaded from this environment, so every part carries "TO CHECK against
the datasheet" in README.md. Sources and comparison results: ../README.md and
../sources/SOURCES.md.

Use from a project: add to its sym-lib-table / fp-lib-table, e.g. for a board two levels
below the repository root:

    (lib (name "KD_Power")(type "KiCad")(uri "${KIPRJMOD}/../../Libraries/KD_Power.pretty")(options "")(descr ""))
"""

import math
import os
import uuid

_NS = uuid.UUID("2d6b8f5e-9c1a-4f7e-8b3d-1a2b3c4d5e01")   # same namespace as Drone_1S_Pico2W: stable tstamps


def uid(name: str) -> str:
    return str(uuid.uuid5(_NS, name))


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
G = 2.54   # symbol grid

# ===================================================================================
# Symbols
# ===================================================================================


def _pin(etype, name, num, x, y, ang, hide=False):
    h = " hide" if hide else ""
    return (f'      (pin {etype} line (at {x:g} {y:g} {ang}) (length 2.54){h}\n'
            f'        (name "{name}" (effects (font (size 1.27 1.27))))\n'
            f'        (number "{num}" (effects (font (size 1.27 1.27))))\n      )')


def _prop(key, val, x, y, hide=False, pid=None):
    h = " hide" if hide else ""
    return (f'    (property "{key}" "{val}" (at {x:g} {y:g} 0)\n'
            f'      (effects (font (size 1.27 1.27)){h})\n    )')


def symbol(name, ref, footprint, datasheet, descr, keywords, left=(), right=(), top=(), bottom=(), width=None):
    """Rectangle symbol. Each side is a list of (name, number, type) or None (gap).
    left/right run top -> bottom, top/bottom run left -> right."""
    rows = max(len(left), len(right), 1)
    cols = max(len(top), len(bottom), 0)
    if width is None:
        longest = max([len(p[0]) for p in list(left) + list(right) if p] + [4])
        width = max(2 * G * round((longest * 1.27 + 2.0) / G), (cols + 1) * G, 5 * G)
    w2 = G * round(width / 2 / G)

    def ext(side):   # room inside the body for the names of top / bottom pins (they read vertically)
        names = [p[0] for p in side if p]
        return G * math.ceil((max(len(n) for n in names) * 1.0 + 1.5) / G) if names else 0
    y0 = G * ((rows - 1) // 2)
    ytop = y0 + G + ext(top)
    ybot = y0 - G * (rows - 1) - G - ext(bottom)
    pins = []
    for i, p in enumerate(left):
        if p:
            pins.append(_pin(p[2], p[0], p[1], -w2 - G, y0 - G * i, 0))
    for i, p in enumerate(right):
        if p:
            pins.append(_pin(p[2], p[0], p[1], w2 + G, y0 - G * i, 180))
    for side, ys, ang in ((top, ytop + G, 270), (bottom, ybot - G, 90)):
        x0 = -G * ((len(side) - 1) // 2)
        for i, p in enumerate(side):
            if p:
                pins.append(_pin(p[2], p[0], p[1], x0 + G * i, ys, ang))
    return f'''  (symbol "{name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
{_prop("Reference", ref, -w2, ytop + 1.27)}
{_prop("Value", name, w2, ytop + 1.27)}
{_prop("Footprint", footprint, 0, ybot - 5.08, True)}
{_prop("Datasheet", datasheet, 0, ybot - 7.62, True)}
{_prop("ki_keywords", keywords, 0, 0, True)}
{_prop("ki_description", descr, 0, 0, True)}
    (symbol "{name}_0_1"
      (rectangle (start {-w2:g} {ytop:g}) (end {w2:g} {ybot:g})
        (stroke (width 0.254) (type default)) (fill (type background))
      )
    )
    (symbol "{name}_1_1"
{chr(10).join(pins)}
    )
  )'''


def write_symlib(fname, syms):
    txt = ('(kicad_symbol_lib (version 20220914) (generator kd_gen_lib)\n'
           + "\n".join(syms) + "\n)\n")
    with open(os.path.join(ROOT, fname), "w") as f:
        f.write(txt)
    print(f"wrote {fname}: {len(syms)} symbols")


PI, PO, BI, IN, PA, OC, NC = "power_in", "power_out", "bidirectional", "input", "passive", "open_collector", "no_connect"
OU = "output"

TI = "https://www.ti.com/lit/ds/symlink/"


def sym_bq25606():
    # RGE VQFN-24 pinout: plus381, psx, openride and decktrix KiCad symbols agree on all 25 pins.
    return symbol(
        "BQ25606", "U", "Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias",
        TI + "bq25606.pdf",
        "Standalone 1-cell 3 A buck battery charger, USB adapter detection (D+/D-), power path, VQFN-24 4x4 mm",
        "charger li-ion 1S buck usb power-path",
        left=[("VBUS", 24, PI), ("VAC", 1, PI), ("PMID", 23, PO), None, ("D+", 3, BI), ("D-", 4, BI), None,
              ("ILIM", 8, PA), ("ICHG", 10, PA), ("VSET", 12, IN), ("~{CE}", 9, IN), ("OTG", 6, IN)],
        right=[("SW", 19, PO), ("SW", 20, PA), ("BTST", 21, PA), ("REGN", 22, PO), None,   # 2nd SW / SYS pin passive (ERC)
               ("SYS", 15, PO), ("SYS", 16, PA), ("BAT", 13, PA), ("BAT", 14, PA), None,
               ("TS", 11, IN), ("STAT", 5, OC), ("~{PG}", 7, OC)],
        bottom=[("NC", 2, NC), ("GND", 17, PI), ("GND", 18, PI), ("EP", 25, PI)])


def sym_tps22997():
    # RYZ WQFN-HR-10: girish, emaneric and teehee KiCad symbols agree on all 10 pins.
    return symbol(
        "TPS22997", "U", "KD_Power:Texas_RYZ0010A_WQFN-HR-10_2x1.5mm_P0.5mm", TI + "tps22997.pdf",
        "Load switch 0.1-5.5 V, 10 A, 4.6 mOhm, power good, adjustable rise time, quick output discharge, WQFN-HR-10 2x1.5 mm",
        "load switch high side power good",
        left=[("VIN", 2, PI), ("VIN", 3, PI), ("VBIAS", 1, PI), None, ("ON", 10, IN), ("CT", 9, PA)],
        right=[("VOUT", 7, PO), ("VOUT", 8, PO), ("QOD", 6, PA), None, ("PG", 4, OC)],
        bottom=[("GND", 5, PI)])


def sym_tps22810():
    # DBV SOT-23-6: official KiCad 9 Power_Management:TPS22810DBV (KiCad 7 has only the DRV variant).
    return symbol(
        "TPS22810DBV", "U", "Package_TO_SOT_SMD:SOT-23-6", TI + "tps22810.pdf",
        "Load switch 2.7-18 V, 2 A, 79 mOhm, adjustable UVLO on EN, thermal shutdown, quick output discharge, SOT-23-6",
        "load switch uvlo",
        left=[("VIN", 1, PI), None, ("EN/UVLO", 3, IN), ("CT", 4, PA)],
        right=[("VOUT", 6, PO), None, ("QOD", 5, PA)],
        bottom=[("GND", 2, PI)])


def sym_tps61235p():
    # RWL VQFN-HR-9: red (Xbox-PMS), cobalt and unsurv KiCad symbols agree on all 9 pins.
    return symbol(
        "TPS61235P", "U", "KD_Power:Texas_RWL_VQFN-HR-9_2.5x2.5mm_P0.5mm", TI + "tps61235p.pdf",
        "Synchronous boost converter, 5.1 V fixed output, 10 A switch, true output disconnect, VQFN-HR-9 2.5x2.5 mm",
        "boost converter 5V output-disconnect",
        left=[("VIN", 3, PI), ("SW", 2, PA), None, ("EN", 7, IN), ("INACT", 8, PA)],
        right=[("VOUT", 9, PO), ("FB", 6, IN), None, ("CC", 4, PA)],
        bottom=[("PGND", 1, PI), ("AGND", 5, PI)])


def sym_bmi088():
    # CONFIRMED against Bosch BST-BMI088-DS001 (rev 1.9) table 14: 4 GNDA, 6 GNDIO (as murex / bit-bots; the Bolt
    # schematic and NxtPX4 label them the other way round). Pin 2 NC is listed "GND" in both SPI and I2C mode:
    # tie it to GND (passive pin, not no-connect). Pin numbers also match the Crazyflie Bolt 1.1 schematic.
    return symbol(
        "BMI088", "U", "KD_Sensors:Bosch_LGA-16_3x4.5mm_P0.5mm",
        "https://www.bosch-sensortec.com/products/motion-sensors/imus/bmi088/",
        "6-axis IMU, 24 g accelerometer + 2000 dps gyroscope, separate chip selects, SPI / I2C, LGA-16 4.5x3 mm",
        "imu accelerometer gyroscope bosch",
        left=[("VDD", 3, PI), ("VDDIO", 11, PI), None, ("PS", 7, IN), ("CSB1", 14, IN), ("CSB2", 5, IN),
              ("SCK", 8, IN), ("SDI", 9, BI)],
        right=[("SDO1", 15, BI), ("SDO2", 10, BI), None, ("INT1", 16, BI), ("INT2", 1, BI), ("INT3", 12, BI),
               ("INT4", 13, BI), ("NC(GND)", 2, PA)],
        bottom=[("GNDA", 4, PI), ("GNDIO", 6, PI)])


def sym_bmp390():
    # Bosch BST-BMP390-DS002 table 52: same pins and LGA-10 2.0 x 2.0 mm pads as the BMP388 (BMP388 is obsolete).
    return symbol(
        "BMP390", "U", "KD_Sensors:Bosch_LGA-10_2x2mm_P0.5mm",
        "https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/bmp390/",
        "Barometric pressure sensor, +-3 Pa, SPI / I2C, LGA-10 2x2 mm (successor of the BMP388, same footprint)",
        "barometer pressure altitude bosch",
        left=[("VDD", 10, PI), ("VDDIO", 1, PI), None, ("CSB", 6, IN), ("SCK", 2, IN), ("SDI", 4, BI)],
        right=[("SDO", 5, BI), None, ("INT", 7, OC)],
        bottom=[("VSS", 3, PI), ("VSS", 8, PI), ("VSS", 9, PI)])


def sym_bmp388():
    # leelili444, Caped-Crussader VENDETTAFC, fdiwth tvc-drone, ArduPilot NxtPX4v2 and the Bitcraze
    # Crazyflie Bolt 1.1 schematic (rev H) agree.
    return symbol(
        "BMP388", "U", "KD_Sensors:Bosch_LGA-10_2x2mm_P0.5mm",
        "https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/bmp388/",
        "Barometric pressure sensor, SPI / I2C, LGA-10 2x2 mm",
        "barometer pressure altitude bosch",
        left=[("VDD", 10, PI), ("VDDIO", 1, PI), None, ("CSB", 6, IN), ("SCK", 2, IN), ("SDI", 4, BI)],
        right=[("SDO", 5, BI), None, ("INT", 7, OC)],
        bottom=[("VSS", 3, PI), ("VSS", 8, PI), ("VSS", 9, PI)])


PICO_PINS = {   # physical pin -> (name, type); Pico 2 W datasheet section 2.1 (same as Pico / Pico W)
    1: ("GP0", BI), 2: ("GP1", BI), 3: ("GND", PI), 4: ("GP2", BI), 5: ("GP3", BI), 6: ("GP4", BI),
    7: ("GP5", BI), 8: ("GND", PI), 9: ("GP6", BI), 10: ("GP7", BI), 11: ("GP8", BI), 12: ("GP9", BI),
    13: ("GND", PI), 14: ("GP10", BI), 15: ("GP11", BI), 16: ("GP12", BI), 17: ("GP13", BI), 18: ("GND", PI),
    19: ("GP14", BI), 20: ("GP15", BI), 21: ("GP16", BI), 22: ("GP17", BI), 23: ("GND", PI), 24: ("GP18", BI),
    25: ("GP19", BI), 26: ("GP20", BI), 27: ("GP21", BI), 28: ("GND", PI), 29: ("GP22", BI), 30: ("RUN", IN),
    31: ("GP26_ADC0", BI), 32: ("GP27_ADC1", BI), 33: ("AGND", PI), 34: ("GP28_ADC2", BI), 35: ("ADC_VREF", PA),
    36: ("3V3_OUT", PO), 37: ("3V3_EN", IN), 38: ("GND", PI), 39: ("VSYS", PI), 40: ("VBUS", PA),
}


def sym_pico2w():
    left = [(PICO_PINS[p][0], p, PICO_PINS[p][1]) for p in range(1, 21)]
    right = [(PICO_PINS[p][0], p, PICO_PINS[p][1]) for p in range(40, 20, -1)]
    # underside pads of the footprint (pad names = pin numbers), confirmed on the module silkscreen
    bottom = [("GND", "TP1", PA), ("USB_DM", "TP2", BI), ("USB_DP", "TP3", BI), ("BOOTSEL", "TP6", IN), None,
              ("SWCLK", "SWCLK", IN), ("GND", "SWD_GND", PA), ("SWDIO", "SWDIO", BI)]
    return symbol(
        "RPi_Pico_2_W", "U", "KD_Modules:RPi_Pico_2_W_SMD_Castellated",
        "https://datasheets.raspberrypi.com/pico/pico-2-w-datasheet.pdf",
        "Raspberry Pi Pico 2 W (RP2350, CYW43439 Wi-Fi/BT), castellated SMD; also the underside test "
        "points TP1-3 (USB), TP6 (BOOTSEL) and SWD pads",
        "raspberry pi pico rp2350 module wifi", left=left, right=right, bottom=bottom, width=22.86)


# ===================================================================================
# Footprints
# ===================================================================================


def line(x1, y1, x2, y2, layer, w):
    return (f'  (fp_line (start {x1:g} {y1:g}) (end {x2:g} {y2:g}) '
            f'(stroke (width {w:g}) (type solid)) (layer "{layer}") (tstamp {uid(f"l{x1}{y1}{x2}{y2}{layer}")}))')


def rect(x1, y1, x2, y2, layer, w):
    return (f'  (fp_rect (start {x1:g} {y1:g}) (end {x2:g} {y2:g}) '
            f'(stroke (width {w:g}) (type solid)) (fill none) (layer "{layer}") (tstamp {uid(f"r{x1}{y1}{x2}{y2}{layer}")}))')


def circle(x, y, r, layer, w, fill=False):
    f = "solid" if fill else "none"
    return (f'  (fp_circle (center {x:g} {y:g}) (end {x + r:g} {y:g}) '
            f'(stroke (width {w:g}) (type solid)) (fill {f}) (layer "{layer}") (tstamp {uid(f"c{x}{y}{r}{layer}")}))')


def text(kind, val, x, y, layer, size=1.0, thick=0.15, ang=0, hide=False):
    h = " hide" if hide else ""
    return (f'  (fp_text {kind} "{val}" (at {x:g} {y:g} {ang}) (layer "{layer}"){h}\n'
            f'    (effects (font (size {size:g} {size:g}) (thickness {thick:g})))\n'
            f'    (tstamp {uid(f"t{kind}{val}{x}{y}{layer}")})\n  )')


def smd(num, shape, x, y, w, h, key, extra="", paste=True):
    layers = '"F.Cu" "F.Paste" "F.Mask"' if paste else '"F.Cu" "F.Mask"'
    return (f'  (pad "{num}" smd {shape} (at {x:g} {y:g}) (size {w:g} {h:g}) '
            f'(layers {layers}){extra} (tstamp {uid(key)}))')


def footprint(name, descr, tags, attr, graphics, pads):
    return (f'(footprint "{name}" (version 20221018) (generator pcbnew)\n  (layer "F.Cu")\n'
            f'  (descr "{descr}")\n  (tags "{tags}")\n  (attr {attr})\n'
            + "\n".join(graphics) + "\n" + "\n".join(pads) + "\n)\n")


def fab_ref(y, size=0.4):
    return text("user", "${REFERENCE}", 0, 0, "F.Fab", size=size, thick=size * 0.15)


def fp_ryz():
    """TPS22997 RYZ0010A WQFN-HR-10, body 1.5 (x) x 2.0 (y) mm, 0.5 mm pitch, no exposed pad.
    Pad centres identical in teehee (noob lib, cites TI MPQF651A) and girish (tmr-lib):
    1-4 on -x (1 and 4 corner pads 0.575 x 0.25, 2-3 = VIN 0.825 x 0.25), 5 at +y,
    6-9 on +x (7-8 = VOUT), 10 at -y. Sizes from teehee."""
    pads = []
    pos = [(1, -0.6625, -0.75, 0.575, 0.25), (2, -0.5375, -0.25, 0.825, 0.25), (3, -0.5375, 0.25, 0.825, 0.25),
           (4, -0.6625, 0.75, 0.575, 0.25), (5, 0.0, 0.9125, 0.25, 0.575), (6, 0.6625, 0.75, 0.575, 0.25),
           (7, 0.5375, 0.25, 0.825, 0.25), (8, 0.5375, -0.25, 0.825, 0.25), (9, 0.6625, -0.75, 0.575, 0.25),
           (10, 0.0, -0.9125, 0.25, 0.575)]
    for n, x, y, w, h in pos:
        pads.append(smd(n, "roundrect", x, y, w, h, f"ryz{n}", " (roundrect_rratio 0.25)"))
    g = [text("reference", "REF**", 0, -1.85, "F.SilkS", size=0.6, thick=0.1),
         text("value", "WQFN-HR-10_2x1.5mm", 0, 1.85, "F.Fab", size=0.4, thick=0.06),
         fab_ref(0, 0.3),
         rect(-0.75, -1.0, 0.75, 1.0, "F.Fab", 0.1),
         line(-0.75, -0.75, -0.5, -1.0, "F.Fab", 0.1),
         circle(-1.15, -1.3, 0.1, "F.SilkS", 0.1, True),                     # pin-1 dot
         rect(-1.2, -1.45, 1.2, 1.45, "F.CrtYd", 0.05)]
    return footprint("Texas_RYZ0010A_WQFN-HR-10_2x1.5mm_P0.5mm",
                     "TI RYZ0010A WQFN-HR-10, 2.0 x 1.5 mm, 0.5 mm pitch (TPS22997). Pads as teehee / girish "
                     "open-source footprints; TO CHECK against TI MPQF651A land pattern",
                     "WQFN-HR TPS22997 RYZ", "smd", g, pads)


def fp_rwl():
    """TPS61235P RWL0009A VQFN-HR-9, body 2.5 x 2.5 mm. CONFIRMED against the TI land pattern example in the
    TPS61235P datasheet (SLVSCK4A p.36): PGND 1 1.1 x 0.3 at (-0.9, -0.77), VOUT 9 1.45 x 0.3 at (0.725, -0.77),
    SW 2 2.9 x 0.3 at y -0.17 with a 0.975 x 0.3 tab centred at y -0.02 (T shape, as asukiaaa), pads 3/8
    0.6 x 0.25 at x +-1.15 / y 0.475, pads 4-7 0.25 x 0.6 at y 1.15, 0.5 mm pitch."""
    pads = []
    pos = [(1, -0.9, -0.77, 1.1, 0.3), (2, 0.0, -0.17, 2.9, 0.3), (3, -1.15, 0.475, 0.6, 0.25),
           (4, -0.75, 1.15, 0.25, 0.6), (5, -0.25, 1.15, 0.25, 0.6), (6, 0.25, 1.15, 0.25, 0.6),
           (7, 0.75, 1.15, 0.25, 0.6), (8, 1.15, 0.475, 0.6, 0.25), (9, 0.725, -0.77, 1.45, 0.3)]
    for n, x, y, w, h in pos:
        pads.append(smd(n, "roundrect", x, y, w, h, f"rwl{n}", " (roundrect_rratio 0.25)"))
    pads.append(smd(2, "rect", 0.0, -0.02, 0.975, 0.3, "rwl2tab"))      # SW pad tab (TI land pattern)
    g = [text("reference", "REF**", 0, -2.0, "F.SilkS", size=0.6, thick=0.1),
         text("value", "VQFN-HR-9_2.5x2.5mm", 0, 2.1, "F.Fab", size=0.4, thick=0.06),
         fab_ref(0, 0.4),
         rect(-1.25, -1.25, 1.25, 1.25, "F.Fab", 0.1),
         line(-1.25, -1.0, -1.0, -1.25, "F.Fab", 0.1),
         line(-1.0, -1.35, 1.0, -1.35, "F.SilkS", 0.12),
         circle(-1.55, -1.25, 0.1, "F.SilkS", 0.1, True),
         rect(-1.75, -1.6, 1.75, 1.7, "F.CrtYd", 0.05)]
    return footprint("Texas_RWL_VQFN-HR-9_2.5x2.5mm_P0.5mm",
                     "TI RWL VQFN-HR-9, 2.5 x 2.5 mm, 0.5 mm pitch (TPS61235P / TPS61236P). Pads as asukiaaa / "
                     "red / unsurv open-source footprints; TO CHECK against the TPS61235P land pattern",
                     "VQFN-HR TPS61235P RWL boost", "smd", g, pads)


# --- Pico 2 W (moved from Drone_1S_Pico2W/tools/gen_libs.py) ------------------------
# Datasheet Fig. 5 origin is the module's bottom-left corner: fx = x - 10.5, fy = 25.5 - y.
# Test points (1.5 x 1.5 mm, 0.3 mm corner radius). Fig. 5 draws two groups; the module's bottom
# silkscreen (photo, Materials/extracted/pico2w_top_bottom_photo.jpg) names them:
#   at the USB end: TP2 (11.5, 49.8) and TP3 (9.5, 49.8) side by side at the edge, TP1 (10.5, 46.5)
#   behind them - TP2 on the pin 21-40 side; column at x = 8: TP4 (41.5), TP5 (39), TP6 (36.5).
# Datasheet 2.1: TP1 GND, TP2 USB DM, TP3 USB DP, TP4 WL_GPIO1 / SMPS PS (do not use),
# TP5 WL_GPIO0 / LED (not recommended), TP6 BOOTSEL.
_TP = {"TP1": (10.5, 46.5), "TP2": (11.5, 49.8), "TP3": (9.5, 49.8),
       "TP4": (8.0, 41.5), "TP5": (8.0, 39.0), "TP6": (8.0, 36.5)}
PICO_TP_ALL = {n: (x - 10.5, 25.5 - y) for n, (x, y) in _TP.items()}
PICO_TP_NAMES = ["TP1", "TP2", "TP3", "TP6"]      # solder pads; TP4 / TP5 get no copper (datasheet: void it)
PICO_TP = [PICO_TP_ALL[n] for n in PICO_TP_NAMES]
# SWD pads E (square) / F / G = SWCLK / GND / SWDIO: confirmed on the module's bottom silkscreen (photo).
PICO_SWD = [(x - 10.5, 25.5 - 19.8) for x in (11.0841, 13.6241, 16.1641)]
PICO_SWD_NAMES = ["SWCLK", "SWD_GND", "SWDIO"]


def fp_pico():
    """Raspberry Pi Pico 2 W castellated: Pico 2 W datasheet Figure 5 (identical to the Pico W
    figure): pads 3.2 x 1.6 mm, 0.79 mm outside the module edge, rows 17.78 mm, 22.58 mm wide,
    USB shell relief pads A-D, test points TP1-3 (USB) and TP6 (BOOTSEL) and SWD pads E-G as solder
    pads; TP4 / TP5 drawn on Fab only (no copper, as the datasheet allows). Module +0.3 mm
    over-paste (datasheet). Origin at the module centre, USB at -Y, pin 1 at -X."""
    pads = []
    px = 9.69
    for p in range(1, 21):
        pads.append(smd(p, "roundrect", -px, -24.13 + 2.54 * (p - 1), 3.2, 1.6, f"pico{p}",
                        " (roundrect_rratio 0.125) (solder_paste_margin 0.3)"))
    for p in range(21, 41):
        pads.append(smd(p, "roundrect", px, 24.13 - 2.54 * (p - 21), 3.2, 1.6, f"pico{p}",
                        " (roundrect_rratio 0.125) (solder_paste_margin 0.3)"))
    for name, (x, y) in zip(PICO_TP_NAMES, PICO_TP):
        pads.append(smd(name, "roundrect", x, y, 1.5, 1.5, f"picotp{name}", " (roundrect_rratio 0.2)"))
    for name, (x, y), shape in zip(PICO_SWD_NAMES, PICO_SWD, ("rect", "circle", "circle")):
        pads.append(smd(name, shape, x, y, 1.5748, 1.5748, f"picoswd{name}"))
    for n, (x, y, w, h) in enumerate([(-2.725, -24.0, 1.1, 1.8), (2.725, -24.0, 1.1, 1.8),
                                      (-2.425, -20.97, 1.05, 1.45), (2.425, -20.97, 1.05, 1.45)]):
        pads.append(smd("", "roundrect", x, y, w, h, f"picousb{n}", " (roundrect_rratio 0.5)", paste=False))
    g = [
        text("reference", "REF**", 0, -28.0, "F.SilkS"),
        text("value", "RPi_Pico_2_W", 0, 0, "F.Fab", ang=90),
        text("user", "${REFERENCE}", 0, -3, "F.Fab", ang=90),
        rect(-10.5, -25.5, 10.5, 25.5, "F.Fab", 0.1),
        rect(-4.0, -26.8, 4.0, -21.5, "F.Fab", 0.1),
        rect(-7.0, 16.5, 7.0, 25.5, "F.Fab", 0.1),
        text("user", "ANTENNA 14x9 KEEP-OUT", 0, 21.0, "F.Fab", size=0.8, thick=0.12),
        text("user", "USB", 0, -19.0, "F.Fab", size=0.8, thick=0.12),
        line(-8.0, -25.3, -4.3, -25.3, "F.SilkS", 0.15),
        line(4.3, -25.3, 8.0, -25.3, "F.SilkS", 0.15),
        line(-10.3, 25.3, -7.6, 25.3, "F.SilkS", 0.15),
        line(7.6, 25.3, 10.3, 25.3, "F.SilkS", 0.15),
        line(-11.5, -25.3, -9.0, -25.3, "F.SilkS", 0.2),
        rect(-11.55, -27.05, 11.55, 25.75, "F.CrtYd", 0.05),
    ]
    for name, (x, y) in PICO_TP_ALL.items():     # all six on Fab; TP4 / TP5 have no copper
        g.append(rect(x - 0.75, y - 0.75, x + 0.75, y + 0.75, "F.Fab", 0.05))
        g.append(text("user", name, x + (0 if name in ("TP2", "TP3") else 1.9), y + (1.3 if name in ("TP2", "TP3") else 0),
                      "F.Fab", size=0.4, thick=0.06))
    for x, y in PICO_SWD:
        g.append(rect(x - 0.79, y - 0.79, x + 0.79, y + 0.79, "F.Fab", 0.05))
    g.append(text("user", "SWD", PICO_SWD[1][0], PICO_SWD[1][1] + 1.6, "F.Fab", size=0.5, thick=0.08))
    return footprint("RPi_Pico_2_W_SMD_Castellated",
                     "Raspberry Pi Pico 2 W, surface-mounted by its castellated pads. Pad geometry per Pico 2 W "
                     "datasheet Fig. 5; TP1-3, TP6 and SWD as solder pads (names from the module silkscreen). No copper under TP4/TP5 or the antenna.",
                     "RPi Pico 2 W RP2350 castellated SMD module", "smd", g, pads)


def fp_bmi088():
    """BMI088 LGA-16, 4.5 x 3.0 x 1.0 mm. Bosch BST-BMI088-DS001 rev 1.9, 8.2 landing pattern: pads 0.25 x 0.675 mm,
    0.5 mm pitch; side pads 1-7 / 9-15 with their inner edge 0.925 mm from the centre (centres +-1.2625 across the
    3.0 mm width), end pads 8 / 16 with their inner edge 1.675 mm from the centre (centres +-2.0125 along the 4.5 mm
    length). Pin 1 at (-1.5, -1.2625) next to the pin-1 corner: 1-7 along -y towards +x, 8 at +x, 9-15 along +y back,
    16 at -x (Bosch fig. 6 top view). (Earlier pads 0.35 x 0.59 from ArduPilot / bit-bots left 0.15 mm gaps.)"""
    pads = []
    yc, xe = 1.2625, 2.0125
    pos = [(-1.5 + 0.5 * k, -yc) for k in range(7)] + [(xe, 0.0)] + \
          [(1.5 - 0.5 * k, yc) for k in range(7)] + [(-xe, 0.0)]
    for n, (x, y) in enumerate(pos, 1):
        w, h = (0.675, 0.25) if n in (8, 16) else (0.25, 0.675)
        pads.append(smd(n, "rect", x, y, w, h, f"bmi{n}"))
    g = [text("reference", "REF**", 0, -2.5, "F.SilkS", size=0.6, thick=0.1),
         text("value", "BMI088", 0, 2.5, "F.Fab", size=0.5, thick=0.08),
         rect(-2.25, -1.5, 2.25, 1.5, "F.Fab", 0.1),
         line(-2.25, -1.0, -1.75, -1.5, "F.Fab", 0.1),
         line(-2.5, -1.85, -1.85, -1.85, "F.SilkS", 0.15),
         rect(-2.6, -1.85, 2.6, 1.85, "F.CrtYd", 0.05)]
    return footprint("Bosch_LGA-16_3x4.5mm_P0.5mm", "Bosch BMI088 LGA-16, 4.5 x 3.0 x 1.0 mm, 0.5 mm pitch, Bosch landing "
                     "pattern (BST-BMI088-DS001 rev 1.9, 8.2)", "Bosch BMI088 IMU LGA", "smd", g, pads)


def fp_bmp388():
    """BMP388 / BMP390 LGA-10, 2.0 x 2.0 x 0.75 mm. Pads 0.25 x 0.275 mm at +-0.7625 = Bosch BMP390 bottom-view pad
    dimensions (BST-BMP390-DS002 7.1/7.2: 1.525 / 1.000 / 0.500 mm spacing, 0.275 x 0.250 side pads) and OpenAXES / the
    KiCad generator footprint from BST-BMP388-DS001. 1-2 on -y, 3-5 on -x, 6-7 on +y, 8-10 on +x."""
    pads = []
    pos = [(0.25, -0.7625), (-0.25, -0.7625), (-0.7625, -0.5), (-0.7625, 0.0), (-0.7625, 0.5),
           (-0.25, 0.7625), (0.25, 0.7625), (0.7625, 0.5), (0.7625, 0.0), (0.7625, -0.5)]
    for n, (x, y) in enumerate(pos, 1):
        w, h = (0.25, 0.275) if abs(y) > 0.7 else (0.275, 0.25)
        pads.append(smd(n, "rect", x, y, w, h, f"bmp{n}"))
    g = [text("reference", "REF**", 0, -1.7, "F.SilkS", size=0.6, thick=0.1),
         text("value", "BMP388", 0, 1.7, "F.Fab", size=0.5, thick=0.08),
         rect(-1.0, -1.0, 1.0, 1.0, "F.Fab", 0.1),
         line(0.5, -1.0, 1.0, -0.5, "F.Fab", 0.1),
         line(0.6, -1.25, 1.2, -1.25, "F.SilkS", 0.15),
         rect(-1.25, -1.25, 1.25, 1.25, "F.CrtYd", 0.05)]
    return footprint("Bosch_LGA-10_2x2mm_P0.5mm", "Bosch BMP388 LGA-10, 2.0 x 2.0 x 0.75 mm, 0.5 mm pitch "
                     "(pads as OpenAXES / KiCad generator from BST-BMP388-DS001; see Libraries/README.md)",
                     "Bosch BMP388 barometer LGA", "smd", g, pads)


def fp_bitcraze_female():
    """Bitcraze female deck connector (bitcraze/hardware female-deck-connector drawing): pads 0.89 x 2.0 mm,
    2.00 mm pitch, staggered +-1.7 mm, body 20.5 x 2.0 x 2.1 mm. Pin 1 at -X, odd pads at -1.7 Y.
    Mates the male deck headers of Crazyflie decks (Flow deck v2 etc.)."""
    pads = []
    for p in range(1, 11):
        pads.append(smd(p, "rect", -9 + 2 * (p - 1), -1.7 if p % 2 else 1.7, 0.89, 2, f"bcf{p}"))
    g = [text("reference", "REF**", 0, -3.6, "F.SilkS", size=0.8, thick=0.12),
         text("value", "Bitcraze female deck connector", 0, 3.6, "F.Fab", size=0.6, thick=0.1),
         rect(-10.25, -1.0, 10.25, 1.0, "F.Fab", 0.1),
         line(-10.7, -2.9, -10.7, 2.9, "F.SilkS", 0.15),
         rect(-10.75, -2.95, 10.75, 2.95, "F.CrtYd", 0.05)]
    return footprint("Bitcraze_FemaleDeck_1x10_P2.00mm_SMD",
                     "Bitcraze female deck connector, 1x10 2.00 mm, SMD, 2.1 mm high (Bitcraze datasheet drawing)",
                     "Bitcraze Crazyflie deck female socket 2.00mm", "smd", g, pads)



# ===================================================================================
# PicoBalancer additions (2026-11-27). Sources in PicoBalancer/Materials/bom_datasheets.
# ===================================================================================


def tht(num, shape, x, y, w, h, drill, key):
    d = f"(drill {drill:g})" if not isinstance(drill, tuple) else f"(drill oval {drill[0]:g} {drill[1]:g})"
    return (f'  (pad "{num}" thru_hole {shape} (at {x:g} {y:g}) (size {w:g} {h:g}) {d} '
            f'(layers "*.Cu" "*.Mask") (tstamp {uid(key)}))')


def npth(x, y, d, key):
    return (f'  (pad "" np_thru_hole circle (at {x:g} {y:g}) (size {d:g} {d:g}) (drill {d:g}) '
            f'(layers "*.Cu" "*.Mask") (tstamp {uid(key)}))')


def sym_bno086():
    # CEVA BNO08X datasheet v1.17 fig. 1-6 pin table (= SparkFun VR IMU breakout v10). RESV_NC 1/7/8/12/13/21-24.
    return symbol(
        "BNO086", "U", "KD_Sensors:CEVA_LGA-28_3.8x5.2mm_P0.5mm",
        "https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf",
        "CEVA BNO086 9-axis IMU with sensor-fusion processor (SH-2), I2C / SPI / UART, LGA-28 3.8 x 5.2 mm",
        "imu bno086 bno085 accelerometer gyroscope magnetometer fusion",
        left=[("VDD", 3, PI), ("VDDIO", 28, PI), None, ("NRST", 11, IN), ("BOOTN", 4, IN), ("PS0/WAKE", 6, IN),
              ("PS1", 5, IN), None, ("CLKSEL0", 10, IN), ("XIN32", 27, PA), ("XOUT32/CLKSEL1", 26, PA), ("CAP", 9, PA)],
        right=[("H_CSN", 18, IN), ("H_SCL/SCLK/RX", 19, IN), ("SA0/H_MOSI", 17, IN), ("H_SDA/H_MISO/TX", 20, BI),
               ("H_INTN", 14, OC), None, ("ENV_SCL", 15, BI), ("ENV_SDA", 16, BI), None,
               ("NC", 1, NC), ("NC", 7, NC), ("NC", 8, NC), ("NC", 12, NC), ("NC", 13, NC), ("NC", 21, NC),
               ("NC", 22, NC), ("NC", 23, NC), ("NC", 24, NC)],
        bottom=[("GND", 2, PI), ("GNDIO", 25, PI)])


def sym_mp6550():
    # MPS MP6550 datasheet rev 1.0 pin functions (p.2-3).
    return symbol(
        "MP6550", "U", "KD_Power:MPS_QFN-12_2x2mm_P0.5mm", "https://www.monolithicpower.com/en/mp6550.html",
        "MPS MP6550 H-bridge motor driver, 1.8-22 V, 2 A, current sense / limit, QFN-12 2x2 mm",
        "motor driver h-bridge mp6550 dc brushed",
        left=[("VIN", 9, PI), None, ("IN1", 1, IN), ("IN2", 10, IN), ("nSLEEP_HB", 12, IN), ("nSLEEP_LDO", 5, IN)],
        right=[("OUT1", 2, PO), ("OUT2", 8, PO), None, ("ISET", 7, PA), ("VISEN", 11, OU), ("VCC", 6, PA),
               ("V3P3", 4, PO)],
        bottom=[("GND", 3, PI)])


def sym_pico_w_socket():
    left = [(PICO_PINS[p][0], p, PICO_PINS[p][1]) for p in range(1, 21)]
    right = [(PICO_PINS[p][0], p, PICO_PINS[p][1]) for p in range(40, 20, -1)]
    return symbol(
        "RPi_Pico_W_Socket", "U", "KD_Modules:RPi_Pico_Socket_2x20_P2.54mm_Vertical",
        "https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf",
        "Raspberry Pi Pico W / Pico 2 W (same 40-pin edge) plugged into two 1x20 2.54 mm sockets",
        "raspberry pi pico w pico2w rp2040 rp2350 socket module", left=left, right=right, width=22.86)


def fp_bno086():
    """CEVA BNO08X LGA-28, 3.8 x 5.2 x 1.1 mm. Landing pattern = BNO08X datasheet v1.17 fig. 7-2 (Bosch): side pads
    0.675 x 0.25 mm flush with the body edge (x +-1.5625), 10 per side at 0.5 mm pitch (y +-0.25 .. +-2.25); top / bottom
    rows 4 pads 0.25 x 0.575 mm (from the edge inward) at x +-0.25 / +-0.75. Top view: pin 1 top-right, then CCW:
    2-5 top row right->left, 6-15 left column top->bottom, 16-19 bottom row left->right, 20-28 right column bottom->top."""
    xs, ys, yr = 1.5625, [-2.25 + 0.5 * k for k in range(10)], 2.3125
    pos = {1: (xs, -2.25)}
    for k, x in enumerate((0.75, 0.25, -0.25, -0.75)):
        pos[2 + k] = (x, -yr)
    for k, y in enumerate(ys):
        pos[6 + k] = (-xs, y)
    for k, x in enumerate((-0.75, -0.25, 0.25, 0.75)):
        pos[16 + k] = (x, yr)
    for k, y in enumerate(reversed(ys)):
        pos[20 + k] = (xs, y)
    pads = []
    for n in range(1, 29):
        x, y = pos[n]
        w, h = (0.25, 0.575) if n in (2, 3, 4, 5, 16, 17, 18, 19) else (0.675, 0.25)
        pads.append(smd(n, "rect", x, y, w, h, f"bno{n}"))
    g = [text("reference", "REF**", 0, -3.4, "F.SilkS", size=0.6, thick=0.1),
         text("value", "BNO086", 0, 3.4, "F.Fab", size=0.5, thick=0.08), fab_ref(0, 0.4),
         rect(-1.9, -2.6, 1.9, 2.6, "F.Fab", 0.1), line(1.4, -2.6, 1.9, -2.1, "F.Fab", 0.1),
         circle(2.25, -2.85, 0.1, "F.SilkS", 0.1, True),
         line(-2.05, -2.75, -1.6, -2.75, "F.SilkS", 0.12), line(-2.05, 2.75, -1.6, 2.75, "F.SilkS", 0.12),
         line(1.6, 2.75, 2.05, 2.75, "F.SilkS", 0.12),
         rect(-2.15, -2.85, 2.15, 2.85, "F.CrtYd", 0.05)]
    return footprint("CEVA_LGA-28_3.8x5.2mm_P0.5mm", "CEVA BNO086 / BNO085 LGA-28, 3.8 x 5.2 mm, 0.5 mm pitch, landing "
                     "pattern from the BNO08X datasheet v1.17 fig. 7-2", "CEVA BNO086 BNO085 IMU LGA", "smd", g, pads)


def fp_mp6550():
    """MPS QFN-12 2 x 2 mm (MP6550GG), no exposed pad. Recommended land pattern, MP6550 datasheet rev 1.0 p.13: side
    pads 0.70 x 0.25 mm centred x +-1.0 (0.65..1.35), y +-0.25 / +-0.75; end pads 0.25 x 0.70 mm at x +-0.25, y +-1.0.
    Top view: 1-4 left column top->bottom, 5-6 bottom row left->right, 7-10 right column bottom->top, 11-12 top row
    right->left (pin 1 = IN1 top-left)."""
    pos = {1: (-1.0, -0.75), 2: (-1.0, -0.25), 3: (-1.0, 0.25), 4: (-1.0, 0.75), 5: (-0.25, 1.0), 6: (0.25, 1.0),
           7: (1.0, 0.75), 8: (1.0, 0.25), 9: (1.0, -0.25), 10: (1.0, -0.75), 11: (0.25, -1.0), 12: (-0.25, -1.0)}
    pads = []
    for n, (x, y) in pos.items():
        w, h = (0.25, 0.70) if n in (5, 6, 11, 12) else (0.70, 0.25)
        pads.append(smd(n, "roundrect", x, y, w, h, f"mp6550_{n}", " (roundrect_rratio 0.25)"))
    g = [text("reference", "REF**", 0, -2.1, "F.SilkS", size=0.6, thick=0.1),
         text("value", "MP6550", 0, 2.1, "F.Fab", size=0.4, thick=0.06), fab_ref(0, 0.3),
         rect(-1.0, -1.0, 1.0, 1.0, "F.Fab", 0.1), line(-1.0, -0.6, -0.6, -1.0, "F.Fab", 0.1),
         circle(-1.6, -1.25, 0.1, "F.SilkS", 0.1, True),
         rect(-1.6, -1.6, 1.6, 1.6, "F.CrtYd", 0.05)]
    return footprint("MPS_QFN-12_2x2mm_P0.5mm", "MPS QFN-12 2 x 2 mm, 0.5 mm pitch, no exposed pad (MP6550GG), land "
                     "pattern from the MP6550 datasheet rev 1.0 p.13", "MPS QFN-12 MP6550", "smd", g, pads)


def fp_keystone_1042():
    """Keystone 1042 / 1042P SMT 18650 holder (drawings 1042 rev H, 1042P rev C - same mounting pad layout): two pads
    >= 6.47 x 7.46 mm with >= 86.80 mm overall (pads 6.5 x 7.5 mm, outer edges at y +-43.4), two locating holes on a
    diagonal 16.00 across x 55.20 along: 2.39 mm near pad 1 (+) and 3.45 mm near pad 2 (-), as placed in the Fusion
    model - WHICH END TAKES WHICH HOLE IS TO VERIFY on a real holder. Pad 1 = + contact (board-centre end, +y).
    Body 77.05 x 20.65 x 14.86 mm."""
    pads = [smd(1, "rect", 0, 39.65, 6.5, 7.5, "k1042p1"), smd(2, "rect", 0, -39.65, 6.5, 7.5, "k1042p2"),
            npth(8.0, 27.6, 2.39, "k1042h1"), npth(-8.0, -27.6, 3.45, "k1042h2")]
    g = [text("reference", "REF**", 0, 0, "F.SilkS", size=1.2, thick=0.18, ang=90),
         text("value", "Keystone_1042", 0, 0, "F.Fab", size=1.0, thick=0.15, ang=90),
         rect(-10.325, -38.525, 10.325, 38.525, "F.Fab", 0.12),
         line(-10.45, -35.5, -10.45, 35.5, "F.SilkS", 0.15), line(10.45, -35.5, 10.45, 35.5, "F.SilkS", 0.15),
         text("user", "+", -6.0, 34.5, "F.SilkS", size=2.0, thick=0.3),
         text("user", "-", -6.0, -34.5, "F.SilkS", size=2.0, thick=0.3),
         rect(-10.7, -43.7, 10.7, 43.7, "F.CrtYd", 0.05)]
    return footprint("Keystone_1042_1x18650_SMD", "Keystone 1042 / 1042P SMT holder for one 18650 cell, pads and "
                     "locating holes from the Keystone drawings (1042 rev H, 1042P rev C)", "battery holder 18650 "
                     "Keystone 1042", "smd", g, pads)


def fp_usb4235():
    """GCT USB4235 USB 2.0 Type-C receptacle, vertical, SMT, 16 pin (drawing rev A 21-08-2024, sheet 2 recommended PCB
    layout): 16 pads 0.30 x 0.87 mm in two rows 0.60 mm apart (edge to edge, centres +-0.735), row A on top (A1, A4-A9,
    A12 left->right), row B below (B12, B9-B4, B1 left->right); outer pads 5.50 mm apart, inner six at 0.50 mm pitch;
    2 x 0.60 mm peg holes 7.50 mm apart; 2 shell tabs in plated slots 0.60 x 0.85 mm (pads 1.10 x 1.35 mm) 10.00 mm
    apart. Drawn for a 1.0 mm PCB (pegs do not protrude on 1.6 mm). TO CHECK: 1:1 print against the part."""
    xs = [-2.75, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 2.75]
    rows = {-0.735: ["A1", "A4", "A5", "A6", "A7", "A8", "A9", "A12"],
            0.735: ["B12", "B9", "B8", "B7", "B6", "B5", "B4", "B1"]}
    pads = []
    for y, names in rows.items():
        for x, n in zip(xs, names):
            pads.append(smd(n, "rect", x, y, 0.30, 0.87, f"u4235{n}"))
    pads += [npth(-3.75, 0, 0.60, "u4235peg1"), npth(3.75, 0, 0.60, "u4235peg2"),
             tht("SH", "oval", -5.0, 0, 1.10, 1.35, (0.60, 0.85), "u4235s1"),
             tht("SH", "oval", 5.0, 0, 1.10, 1.35, (0.60, 0.85), "u4235s2")]
    g = [text("reference", "REF**", 0, -2.6, "F.SilkS", size=0.8, thick=0.12),
         text("value", "USB4235-03-C", 0, 2.6, "F.Fab", size=0.6, thick=0.1), fab_ref(0, 0.5),
         rect(-4.47, -1.58, 4.47, 1.58, "F.Fab", 0.1),
         line(-4.6, -1.7, -3.5, -1.7, "F.SilkS", 0.12), line(3.5, -1.7, 4.6, -1.7, "F.SilkS", 0.12),
         line(-4.6, 1.7, -3.5, 1.7, "F.SilkS", 0.12), line(3.5, 1.7, 4.6, 1.7, "F.SilkS", 0.12),
         rect(-5.8, -1.95, 5.8, 1.95, "F.CrtYd", 0.05)]
    return footprint("USB_C_Receptacle_GCT_USB4235_Vertical", "GCT USB4235 USB 2.0 Type-C receptacle, vertical SMT, "
                     "16 pin, 6.5 mm tall (GCT drawing sheet 2)", "usb type-c receptacle vertical GCT USB4235", "smd",
                     g, pads)


def fp_slide_switch_3pin():
    """Slide switch, SPDT, 3 straight PC pins in line at 2.54 mm, 0.9 mm holes: fits NKK AS12AP (2.54 mm, 0.8 mm
    recommended holes), NKK SS12SDP4 (2.54 mm, 0.6 x 0.4 mm pins) and E-Switch EG1218 (2.50 mm, 0.9 mm holes). Pin 2 =
    common. Pins along y; outline = AS12AP body ~5.4 x 9.8 mm."""
    pads = [tht(n, "rect" if n == 1 else "circle", 0, -2.54 + 2.54 * (n - 1), 1.6, 1.6, 0.9, f"sw3_{n}")
            for n in (1, 2, 3)]
    g = [text("reference", "REF**", 0, -6.2, "F.SilkS", size=0.8, thick=0.12),
         text("value", "SW_Slide_SPDT", 0, 6.2, "F.Fab", size=0.6, thick=0.1),
         rect(-2.7, -4.9, 2.7, 4.9, "F.Fab", 0.1), rect(-2.85, -5.05, 2.85, 5.05, "F.SilkS", 0.12),
         rect(-3.1, -5.3, 3.1, 5.3, "F.CrtYd", 0.05)]
    return footprint("SW_Slide_SPDT_3pin_P2.54mm_Vertical", "Slide switch SPDT, 3 in-line PC pins 2.54 mm, 0.9 mm holes "
                     "(NKK AS12AP / SS12SDP4, E-Switch EG1218)", "switch slide SPDT THT", "through_hole", g, pads)


def fp_littelfuse_1812l():
    """Littelfuse 1812L PolySwitch PPTC: recommended pad layout (1812L datasheet p.6): two 1.78 x 3.15 mm pads, 3.45 mm
    gap (centres +-2.615 mm). Larger than the generic 1812 IPC footprint: trip current depends on the pad heat sinking."""
    pads = [smd(1, "rect", -2.615, 0, 1.78, 3.15, "lf1812p1"), smd(2, "rect", 2.615, 0, 1.78, 3.15, "lf1812p2")]
    g = [text("reference", "REF**", 0, -2.4, "F.SilkS", size=0.8, thick=0.12),
         text("value", "1812L", 0, 2.4, "F.Fab", size=0.6, thick=0.1), fab_ref(0, 0.5),
         rect(-2.25, -1.6, 2.25, 1.6, "F.Fab", 0.1),
         line(-1.6, -1.75, 1.6, -1.75, "F.SilkS", 0.12), line(-1.6, 1.75, 1.6, 1.75, "F.SilkS", 0.12),
         rect(-3.8, -1.9, 3.8, 1.9, "F.CrtYd", 0.05)]
    return footprint("Fuse_Littelfuse_1812L", "Littelfuse 1812L PolySwitch PPTC, datasheet pad layout (1.78 x 3.15 mm "
                     "pads, 3.45 mm gap)", "fuse ptc polyswitch 1812 littelfuse", "smd", g, pads)


def fp_wire_pads_6():
    """Six SMD solder pads for wires, 2.0 mm pitch, 1.5 x 3.0 mm, pad names on silk in the Pololu micro-metal-gearmotor
    encoder order: 1 GND, 2 B, 3 A, 4 VCC, 5 M2, 6 M1 (same numbering as the JST SH 6-pin connector)."""
    names = ["GND", "B", "A", "VCC", "M2", "M1"]
    pads, g = [], [text("reference", "REF**", 0, 3.3, "F.SilkS", size=0.7, thick=0.12, hide=True),
                   text("value", "SolderWire_Pads_1x06", 0, 3.3, "F.Fab", size=0.5, thick=0.08)]
    for k, nm in enumerate(names):
        x = -5.0 + 2.0 * k
        pads.append(smd(k + 1, "rect", x, 0, 1.5, 3.0, f"wp6_{k}", paste=False))
        g.append(text("user", nm, x, -2.3, "F.SilkS", size=0.7, thick=0.12, ang=90 if len(nm) > 2 else 0))
    g.append(rect(-6.0, -3.4, 6.0, 1.75, "F.CrtYd", 0.05))
    return footprint("SolderWire_Pads_1x06_P2.00mm_Named", "6 wire solder pads 1.5 x 3.0 mm, 2.0 mm pitch, named GND B A "
                     "VCC M2 M1 (Pololu encoder order)", "solder wire pads 2.0mm", "smd", g, pads)


def fp_pico_socket():
    """Raspberry Pi Pico W / Pico 2 W on two 1x20 female 2.54 mm sockets (Sullins PPPC201LFBN-RC): rows 17.78 mm apart,
    pads 1.7 mm, 1.0 mm drill. Origin at the module centre, USB at -Y: pin 1 top-left, pins 1-20 down the left side,
    21-40 up the right side (Pico W datasheet fig. 2). Module outline 21 x 51 mm and antenna keep-out on Fab."""
    pads = []
    for p in range(1, 21):
        pads.append(tht(p, "rect" if p == 1 else "oval", -8.89, -24.13 + 2.54 * (p - 1), 1.7, 1.7, 1.0, f"psock{p}"))
    for p in range(21, 41):
        pads.append(tht(p, "oval", 8.89, 24.13 - 2.54 * (p - 21), 1.7, 1.7, 1.0, f"psock{p}"))
    g = [text("reference", "REF**", 0, -27.6, "F.SilkS"),
         text("value", "RPi_Pico_W_Socket", 0, 0, "F.Fab", ang=90), text("user", "${REFERENCE}", 0, -4, "F.Fab", ang=90),
         rect(-10.5, -25.5, 10.5, 25.5, "F.Fab", 0.1), rect(-4.0, -26.8, 4.0, -21.5, "F.Fab", 0.1),
         text("user", "USB", 0, -19.0, "F.Fab", size=0.8, thick=0.12),
         rect(-7.0, 16.5, 7.0, 25.5, "F.Fab", 0.1), text("user", "ANTENNA KEEP-OUT", 0, 21.0, "F.Fab", size=0.8, thick=0.12),
         rect(-10.16, -25.4, -7.62, 25.4, "F.SilkS", 0.12), rect(7.62, -25.4, 10.16, 25.4, "F.SilkS", 0.12),
         rect(-11.0, -26.0, 11.0, 26.0, "F.CrtYd", 0.05)]
    return footprint("RPi_Pico_Socket_2x20_P2.54mm_Vertical", "Raspberry Pi Pico W / Pico 2 W on two 1x20 2.54 mm female "
                     "sockets, rows 17.78 mm", "raspberry pi pico socket 2x20", "through_hole", g, pads)

FOOTPRINTS = {
    "KD_Power": [("Texas_RYZ0010A_WQFN-HR-10_2x1.5mm_P0.5mm", fp_ryz),
                 ("Texas_RWL_VQFN-HR-9_2.5x2.5mm_P0.5mm", fp_rwl),
                 ("MPS_QFN-12_2x2mm_P0.5mm", fp_mp6550), ("Keystone_1042_1x18650_SMD", fp_keystone_1042),
                 ("Fuse_Littelfuse_1812L", fp_littelfuse_1812l)],
    "KD_Sensors": [("Bosch_LGA-16_3x4.5mm_P0.5mm", fp_bmi088), ("Bosch_LGA-10_2x2mm_P0.5mm", fp_bmp388),
                   ("CEVA_LGA-28_3.8x5.2mm_P0.5mm", fp_bno086)],
    "KD_Modules": [("RPi_Pico_2_W_SMD_Castellated", fp_pico), ("RPi_Pico_Socket_2x20_P2.54mm_Vertical", fp_pico_socket)],
    "KD_Connectors": [("Bitcraze_FemaleDeck_1x10_P2.00mm_SMD", fp_bitcraze_female),
                      ("USB_C_Receptacle_GCT_USB4235_Vertical", fp_usb4235),
                      ("SolderWire_Pads_1x06_P2.00mm_Named", fp_wire_pads_6)],
    "KD_Switches": [("SW_Slide_SPDT_3pin_P2.54mm_Vertical", fp_slide_switch_3pin)],
}
SYMBOLS = {
    "KD_Power": [sym_bq25606, sym_tps22997, sym_tps22810, sym_tps61235p, sym_mp6550],
    "KD_Sensors": [sym_bmi088, sym_bmp390, sym_bmp388, sym_bno086],
    "KD_Modules": [sym_pico2w, sym_pico_w_socket],
}


def lib_table_entries(rel):
    """sym/fp lib-table lines for a project at ${KIPRJMOD}/<rel> from the Libraries folder."""
    sym = [f'  (lib (name "{n}")(type "KiCad")(uri "${{KIPRJMOD}}/{rel}/{n}.kicad_sym")(options "")'
           f'(descr "KiCad-Designs shared library"))' for n in SYMBOLS]
    fp = [f'  (lib (name "{n}")(type "KiCad")(uri "${{KIPRJMOD}}/{rel}/{n}.pretty")(options "")'
          f'(descr "KiCad-Designs shared library"))' for n in FOOTPRINTS]
    return sym, fp


if __name__ == "__main__":
    for lib, fps in FOOTPRINTS.items():
        d = os.path.join(ROOT, f"{lib}.pretty")
        os.makedirs(d, exist_ok=True)
        for name, fn in fps:
            with open(os.path.join(d, f"{name}.kicad_mod"), "w") as f:
                f.write(fn())
        print(f"wrote {lib}.pretty: {len(fps)} footprints")
    for lib, syms in SYMBOLS.items():
        write_symlib(f"{lib}.kicad_sym", [s() for s in syms])
