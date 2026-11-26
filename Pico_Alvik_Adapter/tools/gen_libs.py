#!/usr/bin/env python3
"""Generate the project-local symbol library and footprint library."""

import os
from design import LIB, PICO_PINS, NANO_PINS, uid

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)

F127 = "(effects (font (size 1.27 1.27)))"


def pin(etype, name, num, x, y, ang, length=2.54):
    return (f'      (pin {etype} line (at {x:g} {y:g} {ang}) (length {length:g})\n'
            f'        (name "{name}" {F127})\n'
            f'        (number "{num}" {F127})\n      )')


def prop(key, val, x, y, hide=False, ang=0):
    h = " hide" if hide else ""
    return (f'    (property "{key}" "{val}" (at {x:g} {y:g} {ang})\n'
            f'      (effects (font (size 1.27 1.27)){h})\n    )')


def sym_pico():
    pins = []
    for p in range(1, 21):          # left, top -> bottom
        name, t = PICO_PINS[p]
        pins.append(pin(t, name, p, -12.7, 24.13 - 2.54 * (p - 1), 0))
    for p in range(40, 20, -1):     # right, top -> bottom (40 at top)
        name, t = PICO_PINS[p]
        pins.append(pin(t, name, p, 12.7, 24.13 - 2.54 * (40 - p), 180))
    return f'''  (symbol "RPi_Pico_W" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
{prop("Reference", "U", 0, 28.575)}
{prop("Value", "RPi_Pico_W", 0, -28.575)}
{prop("Footprint", f"{LIB}:RPi_Pico_W_SMD_Castellated", 0, -31.115, True)}
{prop("Datasheet", "https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf", 0, -33.655, True)}
    (property "ki_description" "Raspberry Pi Pico W module, castellated SMD mounting, physical pinout" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (symbol "RPi_Pico_W_0_1"
      (rectangle (start -10.16 26.67) (end 10.16 -26.67)
        (stroke (width 0.254) (type default)) (fill (type background))
      )
      (text "USB" (at 0 24.13 0) (effects (font (size 1.27 1.27))))
    )
    (symbol "RPi_Pico_W_1_1"
{chr(10).join(pins)}
    )
  )'''


def sym_nano():
    pins = []
    for i, p in enumerate(range(16, 31)):       # left column top -> bottom
        pins.append(pin("passive", NANO_PINS[p], p, -12.7, 17.78 - 2.54 * i, 0))
    for i, p in enumerate(range(15, 0, -1)):    # right column top -> bottom
        pins.append(pin("passive", NANO_PINS[p], p, 12.7, 17.78 - 2.54 * i, 180))
    return f'''  (symbol "Arduino_Nano_Headers" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
{prop("Reference", "J", 0, 22.225)}
{prop("Value", "Arduino_Nano_Headers", 0, -22.225)}
{prop("Footprint", f"{LIB}:Arduino_Nano_SMD_Headers_Bottom", 0, -24.765, True)}
{prop("Datasheet", "https://docs.arduino.cc/hardware/nano-esp32", 0, -27.305, True)}
    (property "ki_description" "Arduino Nano form-factor 2x15 header (classic Nano pin numbering, Nano ESP32 names)" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (symbol "Arduino_Nano_Headers_0_1"
      (rectangle (start -10.16 20.32) (end 10.16 -20.32)
        (stroke (width 0.254) (type default)) (fill (type background))
      )
      (text "USB" (at 0 17.78 0) (effects (font (size 1.27 1.27))))
    )
    (symbol "Arduino_Nano_Headers_1_1"
{chr(10).join(pins)}
    )
  )'''


def write_symbols():
    txt = ('(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n'
           f'{sym_pico()}\n{sym_nano()}\n)\n')
    with open(os.path.join(PRJ, f"{LIB}.kicad_sym"), "w") as f:
        f.write(txt)


# ---------------------------------------------------------------------------
# Footprints
# ---------------------------------------------------------------------------
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


def fp_pico():
    """Pico W castellated SMD footprint, origin at module centre, USB at -Y.

    Pad geometry from the Pico W datasheet, Figure 5 (SMT footprint):
    pads 3.2 x 1.6 mm extending 0.79 mm outside the module edge,
    pin pitch 2.54 mm, rows 17.78 mm apart (pad centres +-9.69 mm).
    """
    items = []
    px = 9.69
    for p in range(1, 21):
        y = -24.13 + 2.54 * (p - 1)
        items.append(f'  (pad "{p}" smd roundrect (at {-px:g} {y:g}) (size 3.2 1.6) '
                     f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.125) (tstamp {uid(f"pico{p}")}))')
    for p in range(21, 41):
        y = 24.13 - 2.54 * (p - 21)
        items.append(f'  (pad "{p}" smd roundrect (at {px:g} {y:g}) (size 3.2 1.6) '
                     f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.125) (tstamp {uid(f"pico{p}")}))')
    # USB connector shell solder-relief pads A..D (no net, no paste)
    for n, (x, y, w, h) in enumerate([(-2.725, -24.0, 1.1, 1.8), (2.725, -24.0, 1.1, 1.8),
                                       (-2.425, -20.97, 1.05, 1.45), (2.425, -20.97, 1.05, 1.45)]):
        items.append(f'  (pad "" smd roundrect (at {x:g} {y:g}) (size {w:g} {h:g}) '
                     f'(layers "F.Cu" "F.Mask") (roundrect_rratio 0.5) (tstamp {uid(f"picousb{n}")}))')
    g = [
        text("reference", "REF**", 0, -28.0, "F.SilkS"),
        text("value", "RPi_Pico_W_SMD_Castellated", 0, 0, "F.Fab", ang=90),
        text("user", "${REFERENCE}", 0, -3, "F.Fab", ang=90),
        # module outline + USB + antenna area
        rect(-10.5, -25.5, 10.5, 25.5, "F.Fab", 0.1),
        rect(-4.0, -26.8, 4.0, -21.5, "F.Fab", 0.1),
        rect(-7.0, 16.5, 7.0, 25.5, "F.Fab", 0.1),
        text("user", "ANTENNA KEEP-OUT", 0, 21.0, "F.Fab", size=0.8, thick=0.12),
        text("user", "USB", 0, -19.0, "F.Fab", size=0.8, thick=0.12),
        # silkscreen: short edges only (long edges are covered by pads)
        line(-8.0, -25.3, -4.3, -25.3, "F.SilkS", 0.12),
        line(4.3, -25.3, 8.0, -25.3, "F.SilkS", 0.12),
        line(-10.3, 25.3, -7.6, 25.3, "F.SilkS", 0.12),
        line(7.6, 25.3, 10.3, 25.3, "F.SilkS", 0.12),
        # pin-1 marker
        line(-11.5, -25.3, -9.0, -25.3, "F.SilkS", 0.2),
        # courtyard
        rect(-11.55, -27.05, 11.55, 25.75, "F.CrtYd", 0.05),
    ]
    return f'''(footprint "RPi_Pico_W_SMD_Castellated" (version 20221018) (generator pcbnew)
  (layer "F.Cu")
  (descr "Raspberry Pi Pico W, surface-mounted by its castellated edge pads (no through-hole headers). Pad geometry per Pico W datasheet Fig.5. Keep copper away from TP1-TP6, SWD pads and the antenna area.")
  (tags "RPi Pico W castellated SMD module")
  (attr smd)
{chr(10).join(g)}
{chr(10).join(items)}
)
'''


def fp_nano():
    """Nano form-factor SMD male headers for the BOTTOM side.

    The footprint is drawn as seen from the bottom (mirrored), so after it is
    flipped onto B.Cu in the board the pin positions match a real Nano when the
    board is viewed from the top:  pin 1 (D1/TX) bottom-right, pin 16 (D13)
    top-left, USB end at -Y.
    Rows 15.24 mm apart, 2.54 mm pitch, SMD header pads 2.51 x 1.0 mm
    alternating +-1.655 mm about the pin line (KiCad PinHeader_1x15 SMD style).
    """
    items = []
    for p in range(1, 31):
        if p <= 15:            # right column (top view) -> x=-7.62 here (mirrored)
            col, i = -7.62, 15 - p          # i = row index from the top
        else:
            col, i = 7.62, p - 16
        y = -17.78 + 2.54 * i
        dx = 1.655 if (i % 2 == 0) else -1.655
        items.append(f'  (pad "{p}" smd rect (at {col + dx:g} {y:g}) (size 2.51 1) '
                     f'(layers "F.Cu" "F.Paste" "F.Mask") (tstamp {uid(f"nano{p}")}))')
    g = [
        text("reference", "REF**", 0, -21.5, "F.SilkS"),
        text("value", "Arduino_Nano_SMD_Headers_Bottom", 0, 0, "F.Fab", ang=90),
        text("user", "${REFERENCE}", 0, 4, "F.Fab", ang=90),
        # Nano ESP32 board outline (18 x 45 mm) and USB-C
        rect(-9.0, -22.5, 9.0, 22.5, "F.Fab", 0.1),
        rect(-4.5, -23.8, 4.5, -16.5, "F.Fab", 0.1),
        text("user", "NANO USB", 0, -14.5, "F.Fab", size=0.8, thick=0.12),
        # header plastic bodies
        rect(-8.89, -19.05, -6.35, 19.05, "F.Fab", 0.1),
        rect(6.35, -19.05, 8.89, 19.05, "F.Fab", 0.1),
        # silkscreen: header end lines + key pin names
        line(-8.89, -19.2, -6.35, -19.2, "F.SilkS", 0.12),
        line(-8.89, 19.2, -6.35, 19.2, "F.SilkS", 0.12),
        line(6.35, -19.2, 8.89, -19.2, "F.SilkS", 0.12),
        line(6.35, 19.2, 8.89, 19.2, "F.SilkS", 0.12),
        text("user", "TX1", -7.62, 18.4, "F.Fab", size=0.7, thick=0.12),
        text("user", "VIN", 7.62, 18.4, "F.Fab", size=0.7, thick=0.12),
        text("user", "D12", -7.62, -18.4, "F.Fab", size=0.7, thick=0.12),
        text("user", "D13", 7.62, -18.4, "F.Fab", size=0.7, thick=0.12),
        # courtyard: one per header row (centre stays free for other parts)
        rect(-10.8, -19.55, -4.45, 19.55, "F.CrtYd", 0.05),
        rect(4.45, -19.55, 10.8, 19.55, "F.CrtYd", 0.05),
    ]
    return f'''(footprint "Arduino_Nano_SMD_Headers_Bottom" (version 20221018) (generator pcbnew)
  (layer "F.Cu")
  (descr "Arduino Nano footprint as 2x 1x15 2.54mm SMD male pin headers, drawn mirrored for placement on the bottom side (flip left/right). Classic Nano pin numbering: 1=D1/TX ... 15=D12, 16=D13 ... 30=VIN.")
  (tags "Arduino Nano ESP32 SMD pin header bottom")
  (attr smd)
{chr(10).join(g)}
{chr(10).join(items)}
)
'''


def write_footprints():
    d = os.path.join(PRJ, f"{LIB}.pretty")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "RPi_Pico_W_SMD_Castellated.kicad_mod"), "w") as f:
        f.write(fp_pico())
    with open(os.path.join(d, "Arduino_Nano_SMD_Headers_Bottom.kicad_mod"), "w") as f:
        f.write(fp_nano())


def write_lib_tables():
    with open(os.path.join(PRJ, "sym-lib-table"), "w") as f:
        f.write('(sym_lib_table\n'
                f'  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.kicad_sym")'
                '(options "")(descr "Pico Alvik Adapter project symbols"))\n)\n')
    with open(os.path.join(PRJ, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n'
                f'  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.pretty")'
                '(options "")(descr "Pico Alvik Adapter project footprints"))\n)\n')


if __name__ == "__main__":
    write_symbols()
    write_footprints()
    write_lib_tables()
    print("libraries written")
