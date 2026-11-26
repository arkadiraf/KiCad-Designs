"""
Drone_1S_Pico2W - single source of truth for the two boards.

Stage 1 (this revision): bare boards only - outline, drilled holes, the ESC
header pads and the battery tab pads, plus placement guides on the User
layers. Nets, schematic and parts come in later stages (see ../README.md).

Boards
------
* Frame  (Drone_1S_Frame): the 140 mm quad frame, 2.0 mm FR4. Outline and holes
  come from the OpenSCAD design (OpenScad-Designs/Drones/1S_PiZero), exported as
  ../Materials/extracted/1S_PiZero_PCB_outline.dxf (part="pcb_outline").
  Later it carries USB-C + BQ25606 charger, TPS22810 Pico rail switch,
  4x TPS22997 motor switches, TPS61235P 5.1 V boost, the 18650 tab pads and
  the 4 ESCs on pin headers.
* FC     (Drone_1S_FC): the flight-controller module under the frame, in the
  place of the Crazyflie Bolt of the OpenSCAD design: Pico 2 W, BMI088, BMP388,
  Flow deck v2 adapter, JST-SH to the Pi, 2x10 header to the frame.

Coordinates
-----------
OpenSCAD: x forward (camera), y left, z up, origin at the frame centre.
KiCad:    x right, y DOWN.  Board centre is placed at ORIGIN, and
          kicad = (ORIGIN_X + x_scad, ORIGIN_Y - y_scad), viewed from the top,
          so forward points right on screen.
"""

import uuid

_NS = uuid.UUID("2d6b8f5e-9c1a-4f7e-8b3d-1a2b3c4d5e01")


def uid(name: str) -> str:
    """Deterministic UUID so regenerating yields stable files."""
    return str(uuid.uuid5(_NS, name))


ORIGIN_X, ORIGIN_Y = 150.0, 100.0   # board centre on the KiCad sheet (A4 is 297 x 210)


def to_kicad(x, y):
    return ORIGIN_X + x, ORIGIN_Y - y


REVISION = "0.1"
DATE = "2026-11-26"

# ---------------------------------------------------------------------------
# Values copied from 1S_PiZero.scad (OpenScad-Designs @ 115559d). The DXF is
# the geometry source; these are only used to cross-check it and to draw the
# placement guides. If the scad changes, re-export the DXF and update these.
# ---------------------------------------------------------------------------
SCAD = dict(
    wheelbase=140.0,
    motor_hole_pcd=9.0, motor_hole_d=2.2, motor_shaft_hole=4.0,
    motor_bell_d=15.76, prop_d=63.5,
    esc_l=16.2, esc_w=11.0, esc_radius=47.0, esc_pins_in=4, esc_pins_out=3,
    pin_hole=1.0,
    fc_size=(36.0, 35.4), fc_holes=30.5, fc_hole_d=2.7,
    center_l=80.0, center_w=44.0,
    crad_hole=(24.0, 9.45 + 6.0 + 2.05), crad_hole_d=2.2,   # rail_in + rail_w + 2.05
    ph_hole=0.8,
    bat_d=18.4, bat_len=65.2, tab_pad=3.0,
    pi_l=65.0, pi_w=30.0, pi_hole_x=58.0, pi_hole_y=23.0,
)
L = SCAD["wheelbase"] / (2 * 2 ** 0.5)
MOTORS = [(L, L), (L, -L), (-L, -L), (-L, L)]     # scad order (x forward, y left)
MOTOR_NAMES = ["FL", "FR", "RR", "RL"]            # front-left, front-right, rear-right, rear-left

# ---------------------------------------------------------------------------
# Frame board
# ---------------------------------------------------------------------------
FRAME = dict(
    project="Drone_1S_Frame",
    title="1S Pico 2 W drone - frame / power board",
    thickness=2.0,          # user request: 2 mm frame (scad pcb_t is still 1.6)
)

# Hole classes found in the DXF, by nominal diameter (mm). The OpenSCAD circles
# are polygons, so the fitted diameter is snapped to the nearest of these.
HOLE_CLASSES = {
    4.0: "motor_shaft",     # clearance for the shaft end and clip (NPTH)
    2.2: "m2",              # motor M2 screws and cover/gear M2 screws (NPTH)
    2.7: "fc_mount",        # FC module M2.5 screws, 30.5 mm square (NPTH)
    1.0: "esc_pin",         # ESC header pins (plated, electrical)
    0.8: "jst_ph",          # JST PH pins of the Bolt-era connectors (dropped, see README)
}

ESC_PAD = 1.7               # annular pad for the 1.0 mm ESC header holes
TAB_PAD_SIZE = (SCAD["tab_pad"], 10.0)   # battery tab pads, from pcb() in the scad
TAB_PAD_X = SCAD["bat_len"] / 2 + SCAD["tab_pad"] / 2 - 0.5

# ---------------------------------------------------------------------------
# FC module board - a new design (not the Bolt). The frame will be rewired to
# suit it; the 30.5 mm M2.5 pattern is kept only until the frame is redone.
#   TOP side    (faces the frame): Pico 2 W, castellated SMD, nothing else.
#   BOTTOM side (faces the ground): sensor / support ICs and the Crazyflie deck
#               connectors, so the Flow deck v2 plugs in from below exactly as
#               it does under a Crazyflie.
# ---------------------------------------------------------------------------
LIB = "Drone_1S"            # project footprint library (../Drone_1S.pretty, gen_libs.py)

FC = dict(
    project="Drone_1S_FC",
    title="1S Pico 2 W drone - flight controller module",
    thickness=1.6,
    size=(56.0, 35.4),          # 35.4 = old Bolt width (fits the printed landing gear)
    corner_r=2.0,
    holes=SCAD["fc_holes"], hole_d=SCAD["fc_hole_d"],
    pico_size=(51.0, 21.0),
    pico_c=(-2.5, 0.0),          # Pico spans x -28 .. 23; micro-USB at the rear edge (x = -28)
    notch=(14.0, 9.0),           # Pico 2 W datasheet 2.2.1: 14 x 9 mm antenna cut-out
    # Crazyflie deck interface (Bitcraze deck template c8f9a2e): two 1x10 rows,
    # 2.00 mm pitch, 22.0 mm apart, pin 1 of both rows at the FRONT. Deck board
    # 25.2 x 27.3 mm centred on the connector pair. Centred on the FC = frame centre.
    deck_c=(0.0, 0.0),
    deck_rows=22.0,
    deck_board=(25.2, 27.3),     # x (along the rows) by y
)

# Crazyflie 2.x deck connector pinout (docs/cf2_exp_pinout.png in the Bitcraze
# template). Viewed from the top of the drone, front up: LEFT row (scad +y) and
# RIGHT row (scad -y), pin 1 at the front.
DECK_LEFT = ["VCC_3V", "UART1_RX", "UART1_TX", "I2C_SDA", "I2C_SCL",
             "IO_1", "IO_2", "IO_3", "IO_4", "GND"]
DECK_RIGHT = ["UART2_RX", "UART2_TX", "SPI_SCK", "SPI_MISO", "SPI_MOSI",
              "NRF_IO_1", "NRF_WKUP", "NRF_OW", "VCOM", "VUSB"]
# Flow deck v2 use (to verify against the Flow deck v2 schematic before stage 2):
# SPI + a chip select on an IO pin for the PMW3901, I2C for the VL53L1x, and its
# supply from VCOM / VCC_3V.

# ---------------------------------------------------------------------------
# Board-to-board: the FC hangs under the frame on 4 x M2.5 standoffs and plugs
# into it, so it can be pulled off and replaced (nothing soldered between them).
#   FC top    : 2 x male pin header 1x10, 2.00 mm, through-hole (J1 left, J2 right)
#   Frame bot : 2 x female socket 1x10, 2.00 mm, SMD (J5 left, J6 right) - SMD so
#               no pin tails come up under the battery-cover rails on the frame top.
# 2.00 mm because a 2.54 mm 1x10 (25.4 mm + body) runs into the M2.5 standoff
# hexes at x = +-12.35 mm; 2.00 mm (20 mm) clears them.
# Rows at y = +-15: outside the Pico courtyard (+-11.55) and the deck pads on the
# FC bottom (|y| <= 13.4), and the FC-side pin tails stay outside the Flow deck
# board (|y| <= 13.65).  Pin 1 of both rows at the front, pin k at x = 9 - 2(k-1).
# ---------------------------------------------------------------------------
B2B = dict(
    pitch=2.0,
    pins=10,
    row_y=15.0,
    # Board-to-board gap (FC top to frame bottom) = standoff length = socket body
    # height + header plastic height. Pick a matched pair, e.g. a 4.5 mm socket +
    # 1.5 mm header on 6 mm standoffs. Pico 2 W on the FC top is ~4 mm tall at the
    # micro-USB, so 6 mm leaves ~2 mm under the frame: keep tall frame-bottom parts
    # out of the area above the Pico. To confirm with the chosen part datasheets.
    standoff=6.0,
)
B2B_PIN_X = [9.0 - B2B["pitch"] * k for k in range(B2B["pins"])]   # scad x of pins 1..10
