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
# Custom parts come from the repository's shared libraries (KiCad-Designs/Libraries, KD_*): see
# Libraries/README.md. Stock KiCad libraries for everything else.
SHARED_LIBS = "../Libraries"   # relative to the project root Drone_1S_Pico2W/ (KiCad-Designs/Libraries)

# The FC hangs on the SAME four M2 holes that hold the printed battery cover (and the
# Pi Zero on it): one bolt stack per hole, top to bottom:
#   cover boss - frame - M2 standoff (6 mm) - FC - M2 screw from below.
# The landing gear has its own four holes (SCAD gear_hole) so it swaps on its own.
# Hole positions come from the scad (crad_hole = 24, rail_in + rail_w + 2.05).
CRAD = SCAD["crad_hole"]
FC = dict(
    project="Drone_1S_FC",
    title="1S Pico 2 W drone - flight controller module",
    silk_name="Pico 2W Flight Controller V01",
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
        ("U2", "KD_Sensors", "Bosch_LGA-16_3x4.5mm_P0.5mm", "BMI088", (0.0, 0.0), 0),
        ("C1", "Capacitor_SMD", "C_0603_1608Metric", "100n", (0.0, 2.6), 0),
        ("U3", "KD_Sensors", "Bosch_LGA-10_2x2mm_P0.5mm", "BMP390", (-6.0, 0.0), 0),   # BMP388 obsolete -> BMP390, same footprint
        ("C2", "Capacitor_SMD", "C_0603_1608Metric", "100n", (-6.0, 2.1), 0),
    ],
    # J9 SWD, NOT POPULATED: JST-SH 3 (Raspberry Pi 3-pin debug connector style: SWCLK, GND,
    # SWDIO) on the FC bottom at the rear edge, wired from the Pico's SWD pads. Its opening faces
    # the rear edge, so the cable (to the Pi's GPIO for OpenOCD, or a Debug Probe) leaves
    # backwards under the FC, clear of the frame and the landing gear. [ref, footprint, value,
    # (x, y) of the footprint origin, i.e. the mounting-pad line + 1.875]
    swd=("J9", "JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal", "SWD (DNP): SWCLK, GND, SWDIO", (-24.8, 0.0)),
    # SW1 BOOTSEL: a reachable copy of the Pico's own BOOTSEL button (which is on the Pico's top, hidden
    # against the frame once the FC is mounted). Wired from the Pico's TP6 (BOOTSEL, datasheet 2.1:
    # "shorting it low at power-up" enters USB mass-storage mode) to GND. Omron B3U-1000P, 3.0 x 2.5 x
    # 1.6 mm, top-actuated, on the FC BOTTOM next to J9 at the rear edge, so it is pressed from below:
    # the Flow deck only covers |x| <= 10.5. [ref, lib, footprint, value, (x, y) scad, rotation]
    bootsel=("SW1", "Button_Switch_SMD", "SW_SPST_B3U-1000P", "BOOTSEL (Pico TP6 to GND)", (-24.6, -6.2), 0),
)

# Crazyflie 2.x deck connector pinout (docs/cf2_exp_pinout.png in the Bitcraze
# template). Viewed from the top of the drone, front up: LEFT row (scad +y) and
# RIGHT row (scad -y), pin 1 at the front.
DECK_LEFT = ["VCC_3V", "UART1_RX", "UART1_TX", "I2C_SDA", "I2C_SCL",
             "IO_1", "IO_2", "IO_3", "IO_4", "GND"]
DECK_RIGHT = ["UART2_TX", "UART2_RX", "SPI_SCK", "SPI_MISO", "SPI_MOSI",
              "NRF_IO_1", "NRF_WKUP", "NRF_OW", "VCOM", "VUSB"]
# Pin names as the Flow deck v2 schematic (rev A) and Crazyflie Bolt 1.1 schematic (rev H)
# expansion connectors (Materials/): left 2 RX1, 3 TX1; right 1 TX2, 2 RX2.
# Flow deck v2 use (Materials/flow_deck_v2_reva_schematic.pdf), VERIFIED:
#   L1  VCC_3V  -> PMW3901 VCCIO + VL53L1x VCC (Crazyflie supplies 2.8-3.0 V; the Pico gives 3.3 V)
#   L4/L5 I2C   -> VL53L1x (XSHUT pulled up to VCC; GPIO1 not fitted)
#   L8  IO_3    -> PMW3901 CS (IO_1 = Loco deck CS, IO_4 = micro-SD deck CS: free here)
#   R3-R5 SPI   -> PMW3901 SCK / MISO / MOSI (RESET, MOTION not fitted)
#   R8  NRF_OW  -> DS28E05 1-wire deck ID EEPROM (optional for us)
#   R9  VCOM    -> TLV70218 LDO -> 1.8 V PMW3901 core. Bolt: VCOM = VBAT (or 5 V) up to 400 mA.
#   L10 GND     (the only ground pin; R6/R7, UARTs, VUSB unused)

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

# Board-to-board pin budget (20 pins), 2026-11-26:
#  - the Pi Zero 2 W is the Pico's USB host (programming with picotool, serial link, boot /
#    shutdown handshake over USB; no PI_STATUS line), so USB D+/D- cross to the frame (J7);
#  - SWD does NOT cross: it goes to J9 on the FC itself (to the Pi's GPIO or a debugger);
#  - so the four motor-switch ON lines stay separate (staggered turn-on, a faulted ESC can
#    be switched off alone), and three GND.
B2B_SIGNALS = ["VSYS", "GND", "GND", "GND",
               "ON1", "ON2", "ON3", "ON4", "PG1", "PG2", "PG3", "PG4",
               "DSHOT1", "DSHOT2", "DSHOT3", "DSHOT4",
               "BOOST_EN", "CHG_PG", "USB_DP", "USB_DM"]
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
]


# ---------------------------------------------------------------------------
# Frame (power board) bill of materials - the electrical parts still to place.
# Already on the board: BT1 tabs, J1-J4 ESC headers, J5/J6 FC sockets, J7 Pi USB,
# J8 Pi 5.1 V, mounting holes. Values from the design doc (Materials/); the ones
# marked "TO CHECK" need the TI datasheet (not downloadable from this environment).
# [refs, value, symbol, footprint, role]
# ---------------------------------------------------------------------------
_R, _C = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric"
_C08 = "Capacitor_SMD:C_0805_2012Metric"
_C12 = "Capacitor_SMD:C_1206_3216Metric"   # passives rule: see the repository README
FRAME_BOM = [
    # --- charger: BQ25606 from USB-C ---
    ("J10", "USB-C receptacle (GCT USB4105-GF-A)", "Connector:USB_C_Receptacle_USB2.0_16P",
     "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal", "charging input, USB 2.0 D+/D- to the charger"),
    ("U1", "BQ25606", "KD_Power:BQ25606",
     "Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias", "1S 3 A standalone charger, power path"),
    # Wurth WE-MAPI 74438357010 (Digi-Key stock): 1 uH +-20 %, Isat 6.2 A (10 %), RDC 13.5 mOhm max,
    # 4.1 x 4.1 x 3.1 mm max; land pattern 1 of its datasheet = KiCad L_Wuerth_MAPI-4030. No vias/traces under it.
    ("L1", "1uH, Isat 6.2 A (Wurth 74438357010)", "Device:L", "Inductor_SMD:L_Wuerth_MAPI-4030", "charger buck inductor"),
    ("R1 R2", "5.1k", "Device:R", _R, "USB-C CC1 / CC2 pull-downs (sink)"),
    ("R3", "226", "Device:R", _R, "ICHG: 3.0 A charge current (doc)"),
    ("R4", "150", "Device:R", _R, "ILIM: 3.2 A input limit (doc)"),
    # BQ25606 datasheet SLUSCK6C 9.3.5: 0-60 C window for the 103AT-2: RT1 5.23 k REGN->TS, RT2 30.9 k TS->GND
    # (the application diagram shows 30.1 k; the worked example gives 30.9 k - used here).
    ("R5", "5.23k", "Device:R", _R, "TS divider top, REGN -> TS (0-60 C window)"),
    ("R6", "30.9k", "Device:R", _R, "TS divider bottom, TS -> GND"),
    # Semitec 103AT-2 (AT series datasheet p.12-13): 10.0 k +-1 % at 25 C, B25/85 3435 K +-1 %, radial resin
    # body 3.7 x 2.4 x 4.0 mm max, 0.5 mm square tin-plated leads (0.71 mm diagonal) at 2.54 mm, 17 mm long.
    # -> 2.54 mm pitch, 1.0 mm drill. Stands next to the cell, bead bent onto it and taped.
    ("TH1", "10k NTC 103AT-2", "Device:Thermistor_NTC", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     "cell temperature for the BQ25606 TS pin (0-60 C window with R5/R6)"),
    # Datasheet pin table: 1 uF on VBUS close to the IC, 10 uF on PMID; 10.2.2.2: ~22 uF input for 3 A charging
    # -> 2 x 10 uF on PMID (the input capacitor of the buck, placed first in the layout order).
    ("C1", "1uF 25V", "Device:C", _C, "VBUS, close to pin 24 (VBUS up to 13.5 V)"),
    ("C2 C23", "10uF 16V", "Device:C", _C08, "PMID, buck input (~22 uF total for 3 A)"),
    ("C3 C4", "10uF 16V", "Device:C", _C08, "SYS"),
    ("C5", "10uF 16V", "Device:C", _C08, "BAT"),
    ("C6", "4.7uF 10V", "Device:C", _C, "REGN"),
    ("C7", "47nF 16V", "Device:C", _C, "BTST bootstrap"),
    ("D1", "LED red 0805", "Device:LED", "LED_SMD:LED_0805_2012Metric", "STAT charge indicator (optional), from SYS as TI's diagram"),
    ("R7", "2.2k", "Device:R", _R, "STAT LED series resistor (STAT sinks 6 mA max)"),
    # --- logic rail: TPS22810 + slide switch ---
    ("U2", "TPS22810DBV", "KD_Power:TPS22810DBV", "Package_TO_SOT_SMD:SOT-23-6", "Pico VSYS switch, 2.54 V UVLO"),
    # APEM MA12R/TR (Digi-Key 563-1102-1-ND), replaces the C&K PCM12SMTR (last-time buy). Same land pattern:
    # terminals 0.7 x 1.5 mm at -2.25 / +0.75 / +2.25 mm, 2 x 0.9 mm bosses 3.0 mm apart, 4 shell tabs - checked
    # against the APEM drawing and BetzDrive's apem-MA12RTR footprint. Common = middle terminal (pad 2 = pin B).
    # Body 6.7 x 2.6 x 1.4 mm, right-angle actuator 1.3 mm out of the side opposite the terminals: that side faces
    # the frame edge. 300 mA / 4 VDC contact rating (EN signal only, uA), -10..+60 C operating.
    ("SW1", "SPDT slide (APEM MA12R/TR)", "Switch:SW_SPDT", "Button_Switch_SMD:SW_SPDT_PCM12", "power switch on EN/UVLO (signal only)"),
    ("C8 C9", "1uF 16V", "Device:C", _C, "TPS22810 VIN / VOUT"),
    ("R8 R9 R10", "156k / 100k / 1.27M (DNP option)", "Device:R", _R,
     "external 2.70 / 3.30 V UVLO divider instead of the internal lockout (doc open item)"),
    # --- motor switches: 4 x TPS22997 ---
    ("U3 U4 U5 U6", "TPS22997", "KD_Power:TPS22997", "KD_Power:Texas_RYZ0010A_WQFN-HR-10_2x1.5mm_P0.5mm",
     "per-ESC high-side switch, ~7.5 A"),
    ("C10 C11 C12 C13", "10uF 16V", "Device:C", _C08, "TPS22997 VIN, at the pins"),
    # TPS22997 datasheet (SLVSGT0) 8.3.2: tR = (0.1302 VIN + 0.0063) CT + 27.8 VIN + 30.5 us -> 3.3 nF at 4.2 V
    # = ~2.0 ms (inrush ~40 mA into ~20 uF of ESC capacitance). CT pin reaches 15 V: capacitor rated >= 30 V.
    ("C14 C15 C16 C17", "3.3nF 50V", "Device:C", _C, "CT soft-start ~2 ms (>= 30 V rating, datasheet)"),
    ("R11 R12 R13 R14", "100k", "Device:R", _R, "ON pull-downs: Pico off = motors off"),
    ("R15 R16 R17 R18", "47k (or Pico internal pull-ups)", "Device:R", _R,
     "PG pull-ups: 3V3 is not on the B2B header - place on the FC or use Pico pull-ups (TO DECIDE)"),
    # --- optional 5.1 V boost for the Pi Zero ---
    ("U7", "TPS61235P", "KD_Power:TPS61235P", "KD_Power:Texas_RWL_VQFN-HR-9_2.5x2.5mm_P0.5mm", "5.1 V boost, true disconnect"),
    # TPS61235P datasheet SLVSCK4A: FB (6) to VOUT on the fixed 5.1 V part; INACT (8) to AGND (unused); EN (7)
    # must not float (100 k pull-down, <= 1 M); VIN <= VOUT - 0.6 = 4.5 V; L 0.7-1.3 uH effective; CI >= 4.7 uF and
    # CO >= 20 uF effective (after DC-bias derating).
    ("L2", "1uH, Isat 6.2 A (Wurth 74438357010)", "Device:L", "Inductor_SMD:L_Wuerth_MAPI-4030",
     "boost inductor (peak ~5.3 A at 2.5 A out, 3.0 V in)"),
    ("C18 C19", "10uF 16V", "Device:C", _C08, "boost input"),
    ("C20 C21 C22", "22uF 10V (TO CHECK)", "Device:C", _C12, "boost output"),
    ("R19", "100k", "Device:R", _R, "BOOST_EN pull-down: Pico off = Pi off"),
    # IOUT_CC = 1.244 V / RCC x 100000 -> 49.9 k = 2.49 A (E24 51 k = 2.44 A); 10 nF in parallel (datasheet).
    # CC mode suits resistive / power-managed loads: 2.5 A is a fault limit above the Pi Zero 2 W's draw.
    ("R20", "49.9k", "Device:R", _R, "boost CC (output current limit) 2.49 A"),
    ("C24", "10nF 16V", "Device:C", _C, "CC pin, in parallel with R20 (datasheet: 10 nF)"),
]
