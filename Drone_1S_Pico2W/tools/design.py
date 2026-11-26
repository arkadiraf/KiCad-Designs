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
    center_l=80.0, center_w=44.0,
    crad_hole=(24.0, 9.45 + 6.0 + 2.05), crad_hole_d=2.2,   # rail_in + rail_w + 2.05 (cover + FC standoffs)
    gear_hole=(35.0, 18.5),                                 # landing-gear skids, own M2 holes
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
    2.7: "fc_mount",        # old Bolt M2.5 pattern (removed from the scad; none expected)
    1.0: "esc_pin",         # ESC header pins (plated, electrical)
    0.75: "jst_ph",         # JST PH pins of J8, Pi 5.1 V (JST ePH drill)
}

ESC_PAD = 1.7               # annular pad for the 1.0 mm ESC header holes
TAB_PAD_SIZE = (SCAD["tab_pad"], 10.0)   # battery tab pads, from pcb() in the scad
TAB_PAD_X = SCAD["bat_len"] / 2 + SCAD["tab_pad"] / 2 - 0.5

# ---------------------------------------------------------------------------
# FC module board - a new design (not the Bolt). The frame will be rewired to
# suit it.
#   TOP side    (faces the frame): Pico 2 W, castellated SMD, nothing else.
#   BOTTOM side (faces the ground): sensor / support ICs and the Crazyflie deck
#               connectors, so the Flow deck v2 plugs in from below exactly as
#               it does under a Crazyflie.
# ---------------------------------------------------------------------------
LIB = "Drone_1S"            # project footprint library (../Drone_1S.pretty, gen_libs.py)

# The FC hangs on the SAME four M2 holes that hold the printed battery cover (and the
# Pi Zero on it): one bolt stack per hole, top to bottom:
#   cover boss - frame - M2 standoff (6 mm) - FC - M2 screw from below.
# The landing gear has its own four holes (SCAD gear_hole) so it swaps on its own.
# Hole positions come from the scad (crad_hole = 24, rail_in + rail_w + 2.05).
CRAD = SCAD["crad_hole"]
FC = dict(
    project="Drone_1S_FC",
    title="1S Pico 2 W drone - flight controller module",
    thickness=1.6,
    holes=[(sx * CRAD[0], sy * CRAD[1]) for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1))],
    hole_d=SCAD["crad_hole_d"],  # 2.2 mm, M2
    ear_r=3.2,                   # board radius round each hole (M2 standoff hex 4 mm AF: 2.31 to the corners)
    pico_size=(51.0, 21.0),
    pico_c=(-2.5, 0.0),          # Pico spans x -28 .. 23; micro-USB at the rear edge (x = -28)
    notch=(14.0, 9.0),           # Pico 2 W datasheet 2.2.1: 14 x 9 mm antenna cut-out
    # Minimum outline = union of
    #   the Pico band     x -28 .. 23, |y| <= 12.5 (Pico lands reach |y| 11.29, + edge clearance and its silk)
    #   the middle block  |x| <= 12.5, |y| <= 16.5 (deck pads |y| <= 13.4, B2B header pads |y| <= 15.7, + silk)
    #   four ears         capsule from each hole to the band, radius ear_r
    # minus the antenna notch, all corners filleted 1 mm.
    band=(-28.0, 23.0, 12.5),
    middle=(12.5, 16.5),
    ear_root=(20.0, 10.0),       # |x|, |y| where each ear joins the band
    fillet=1.0,
    # Crazyflie deck interface (Bitcraze deck template c8f9a2e): two 1x10 rows,
    # 2.00 mm pitch, 22.0 mm apart, pin 1 of both rows at the FRONT.
    deck_c=(0.0, 0.0),
    deck_rows=22.0,
    deck_board=(21.079, 27.94),  # Flow deck v2, x (along the rows) by y: Bitcraze mechanical drawing
    # [ref, lib, footprint, value, (x, y) scad, rotation] - all on the FC BOTTOM, between the
    # deck rows (|x| <= 9, |y| <= 8.6 clear of the deck header pads), under the Flow deck.
    sensors=[
        ("U2", LIB, "Bosch_LGA-16_3x4.5mm_P0.5mm", "BMI088", (0.0, 0.0), 0),
        ("C1", "Capacitor_SMD", "C_0402_1005Metric", "100n", (0.0, 2.6), 0),
        ("U3", LIB, "Bosch_LGA-10_2x2mm_P0.5mm", "BMP388", (-6.0, 0.0), 0),
        ("C2", "Capacitor_SMD", "C_0402_1005Metric", "100n", (-6.0, 2.1), 0),
    ],
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
# Board-to-board: the FC hangs under the frame on the 4 shared M2 holes and plugs
# into it, so it can be pulled off and replaced (nothing soldered between them).
#   FC top    : 2 x male pin header 1x10, 2.00 mm, through-hole (J1 left, J2 right)
#   Frame bot : 2 x Bitcraze female deck connector 1x10, 2.00 mm, SMD, 2.1 mm high
#               (J5 left, J6 right) - the same part as on the Flow deck; SMD pads only,
#               no holes, so nothing comes up under the battery-cover rails.
# Height (low profile, standard standoff): the Pico 2 W's micro-USB reaches 3.73 mm above
# the FC (KiCad-RP-Pico 3D model), so the lowest standard M2 standoff that clears it is
# 5 mm (1.2 mm left). Mated: 2.0 mm male plastic + 2.1 mm socket = 4.1 mm + 0.9 mm air;
# the male pin (Bitcraze short pins, long side up) is trimmed to ~2.8 mm above its plastic
# so it enters the socket ~1.9 mm.
# 2.00 mm keeps the FC's middle block narrow (|x| <= 12.5); 2.54 mm would also fit
# between the shared holes at x = +-24 but widens the board.
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
    standoff=5.0,                # FC top to frame bottom = M2 standoff (lowest standard length over the Pico USB)
    male_plastic=2.0,            # FC header plastic (Bitcraze pins: 2 mm)
    male_pin=2.8,                # mating pin above the plastic, after trimming
    socket_h=2.1,                # Bitcraze female deck connector
    pico_top=3.73,               # Pico micro-USB top above the FC top (KiCad-RP-Pico Pico.wrl)
)
B2B_PIN_X = [9.0 - B2B["pitch"] * k for k in range(B2B["pins"])]   # scad x of pins 1..10

# Board-to-board pin budget (20 pins), decided 2026-11-26:
#  - the Pi Zero 2 W is the Pico's USB host (programming with picotool, serial link, boot /
#    shutdown handshake), so USB D+/D- replace the Pi UART;
#  - SWD crosses too, for recovery from the Pi (J9 on the frame, not fitted by default);
#  - to fit, the motor switches' ON lines are paired: ON_A = front pair, ON_B = rear pair
#    (design doc: one GPIO may drive all four; turn-on stays staggered pair by pair with each
#    channel's CT soft-start; the four PG lines still name a faulted ESC);
#  - no PI_STATUS line (dropped 2026-11-26): the boot / shutdown handshake runs over USB
#    (enumeration = Pi up; shutdown command, then the USB link stopping = safe to cut, plus a
#    grace period and timeout); the freed pin is a third GND.
B2B_SIGNALS = ["VSYS", "GND", "GND", "GND",
               "ON_A", "ON_B", "PG1", "PG2", "PG3", "PG4",
               "DSHOT1", "DSHOT2", "DSHOT3", "DSHOT4",
               "BOOST_EN", "CHG_PG", "USB_DP", "USB_DM", "SWCLK", "SWDIO"]
assert len(B2B_SIGNALS) == 2 * B2B["pins"]

# Frame-top connectors to the Pi Zero 2 W (design doc: 5.1 V separately, UART + status on
# a 4-pin JST-SH with 1 k series resistors). [ref, lib, footprint, value, (x, y), rotation]
FRAME_CONN = [
    # J7 Pi USB: the Pi Zero 2 W is the USB host for the Pico (programming with picotool,
    # USB serial link, boot/shutdown handshake). No VBUS: the Pico runs from VSYS, and VBUS
    # would back-feed VSYS through the Pico's Schottky. 4 pins (GND, D-, D+, GND) so it cannot be
    # confused with the 3-pin SWD connector J9.
    ("J7", "Connector_JST", "JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
     "Pi USB: GND, D-, D+, GND", (5.0, 18.3), 180),
    # J9 SWD, NOT POPULATED: Raspberry Pi 3-pin debug connector style (SWCLK, GND, SWDIO), for
    # recovery from the Pi's GPIO (OpenOCD) or a Raspberry Pi Debug Probe.
    ("J9", "Connector_JST", "JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal",
     "SWD (DNP): SWCLK, GND, SWDIO", (12.5, 18.3), 180),
]
