"""FC hand routing (stage 3): escapes of the two 0.5 mm-pitch Bosch LGAs, imported by gen_pcb.py.

Design coordinates (scad: x forward, y left, mm), as seen from the TOP; the sensors sit on the bottom (B.Cu).

T(net, width, points..., layer="B")   track through the points
V(net, x, y, d=0.6, drill=0.3)        via

The router (router.py) works on a 0.2 mm grid with 0.2 mm clearance, so it cannot leave a 0.5 mm-pitch pad.
These stubs carry every sensor pin to a point the router can reach (a via, or a free stub end); the router
then joins them (it treats this copper as part of each net). Clearances here were laid out by hand for
>= 0.25 mm between foreign copper (DRC minimum 0.15, OSH Park 6 mil); KiCad DRC re-checks everything.

U2 BMI088 (rotated 180): signal row at y = -1.263 (x -1.5 .. 1.5 = pins 9..15), supply / GND row at y = +1.263
(pins 1..7 at x 1.5 .. -1.5), SCK pin 8 at x -2.012, INT1 pin 16 at x +2.012. Inside the package (between the
rows, under the body) two short bars tie the GND pins and the two SDO pins, with a tented GND via between them.
U3 BMP390: 2 x 2 mm, pads at +-0.5 / +-0.763 around (-6, 0).
"""
TRACKS, VIAS = [], []
W = 0.2          # escape width


def T(net, w, *pts, layer="B"):
    TRACKS.append((net, layer, w, pts))


def V(net, x, y, d=0.6, drill=0.3):
    VIAS.append((net, x, y, d, drill))


# ------------------------------------------------------------------ U2 BMI088 --------------------------------------
# signal row (y -1.263) -> staggered vias: row A y -2.6 (x -2.3, -0.5, 1.3), row B y -3.7 (x -1.4, 0.4)
T("SPI0_MOSI", W, (-1.5, -1.263), (-1.5, -1.8), (-2.3, -2.6));              V("SPI0_MOSI", -2.3, -2.6)
T("SPI0_MISO", W, (-1.0, -1.263), (-1.0, -2.0), (-1.4, -2.4), (-1.4, -3.7)); V("SPI0_MISO", -1.4, -3.7)
T("SPI0_MISO", W, (1.5, -1.263), (1.5, -0.55), (-1.0, -0.55), (-1.0, -1.263))   # SDO1 (15) + SDO2 (10), under the body
T("3V3_SENS", W, (-0.5, -1.263), (-0.5, -2.6));                              V("3V3_SENS", -0.5, -2.6)
T("IMU_INT_GYR", W, (0.0, -1.263), (0.0, -2.0), (0.4, -2.4), (0.4, -3.7));    V("IMU_INT_GYR", 0.4, -3.7)
T("IMU_CS_ACC", W, (1.0, -1.263), (1.0, -1.8), (1.3, -2.1), (1.3, -2.6));     V("IMU_CS_ACC", 1.3, -2.6)
# end pins
T("SPI0_SCK", W, (-2.012, 0.0), (-3.0, 0.0));                                 V("SPI0_SCK", -3.0, 0.0)
T("IMU_INT_ACC", W, (2.012, 0.0), (2.5, 0.0), (2.9, -0.4), (2.9, -0.95));     V("IMU_INT_ACC", 2.9, -0.95)
# supply / GND row (y +1.263): GND pins 2, 4, 6, 7 -> bar under the body -> tented via
for x in (1.0, 0.0, -1.0, -1.5):
    T("GND", W, (x, 1.263), (x, 0.55))
T("GND", W, (-1.5, 0.55), (1.0, 0.55))
V("GND", -0.25, 0.25)
T("3V3_SENS", W, (0.5, 1.263), (0.5, 2.675))                                  # VDD -> C1 pad 1
T("GND", W, (0.5, 4.225), (0.5, 5.1));                                        V("GND", 0.5, 5.1)   # C1 pad 2
T("IMU_CS_GYR", W, (-0.5, 1.263), (-0.5, 2.0), (-0.8, 2.3), (-0.8, 2.7));     V("IMU_CS_GYR", -0.8, 2.7)

# ------------------------------------------------------------------ U3 BMP390 --------------------------------------
# 3V3_SENS: VDD (10) + VDDIO (1) at the -y / +x corner, SDO (5) + CSB (6) at the +y / -x corner, both to C2 pad 1
T("3V3_SENS", W, (-5.238, -0.5), (-5.238, -1.0), (-5.75, -1.0), (-5.75, -0.763))
T("3V3_SENS", W, (-5.238, -1.0), (-4.0, -1.0), (-4.0, 2.1), (-5.225, 2.1))
T("3V3_SENS", W, (-6.762, 0.5), (-7.2, 0.5), (-7.2, 1.0), (-6.25, 1.0), (-6.25, 0.763))
T("3V3_SENS", W, (-6.25, 1.0), (-6.25, 1.3), (-5.6, 1.3), (-5.6, 1.7))
# GND: VSS 8 + 9 (+x side) and VSS 3 (-x side), each to a via
T("GND", W, (-5.238, 0.5), (-5.238, 0.0))
T("GND", W, (-5.238, 0.25), (-4.75, 0.25));                                   V("GND", -4.75, 0.25)
T("GND", W, (-6.762, -0.5), (-7.05, -0.8), (-7.05, -1.2));                    V("GND", -7.05, -1.2)
T("GND", W, (-6.775, 2.1), (-7.6, 2.1), (-7.6, 2.9));                         V("GND", -7.6, 2.9)   # C2 pad 2
# I2C out to free stub ends (the router continues from there)
T("I2C_SDA", W, (-6.762, 0.0), (-7.8, 0.0))
T("I2C_SCL", W, (-6.25, -0.763), (-6.25, -2.0))

# ------------------------------------------------------------------ DShot (GP19..GP16 -> R3..R6 -> J1.1..J1.4) -----
# Each Pico pin goes out on top to a via just outside its land (|y| 12.0, inside the widened Pico band), down to its
# 100R on the bottom, then the four lines nest without crossing: lower levels for the pins further forward, up to J1
# through the gaps between the Flow deck P1 pads (columns x 10 / 8 / 6 / 4). Levels stay >= 7.6 on the antenna-notch
# prongs (x > 14, board edge at |y| 7) and <= 8.3 where they pass the P1 pads (bottom edge 8.65).
_DS = [  # (pin x, net index, [down-path points after the resistor's DSHOT pad], column, J1 pad x)
    (11.47, 1, [(11.47, 9.0), (10.0, 9.0)], 10.0, 9.0),
    (14.01, 2, [(14.01, 8.5), (10.4, 8.5), (9.65, 7.75), (8.0, 7.75)], 8.0, 7.0),
    (19.09, 3, [(19.09, 8.05), (12.6, 8.05), (11.85, 7.3), (6.0, 7.3)], 6.0, 5.0),
    (21.63, 4, [(21.63, 7.6), (13.8, 7.6), (13.05, 6.85), (4.0, 6.85)], 4.0, 3.0),
]
for x, k, path, col, jx in _DS:
    T(f"DSHOT{k}_MCU", 0.25, (x, 10.5), (x, 12.0), layer="F")       # from inside the Pico land to the via
    V(f"DSHOT{k}_MCU", x, 12.0)
    T(f"DSHOT{k}_MCU", 0.25, (x, 12.0), (x, 11.225))                  # via -> resistor pad 1 (bottom)
    T(f"DSHOT{k}", 0.25, (x, 9.575), *path, (col, 13.9), (jx + 0.3, 14.6))

# 3V3 to the Flow deck VCC (P1.1), boxed in by the DShot columns on the bottom: up through a via between them
T("3V3", 0.4, (9.0, 9.825), (9.0, 12.4))
V("3V3", 9.0, 12.4)

# ------------------------------------------------------------------ ON1..ON3 (GP13..GP15 -> J2.1..J2.3) -------------
# Mirror of the DShot scheme on the -y prong: via just outside the land, nested levels on the bottom, up to J2 through
# the gaps between the P2 pads (columns x 10 / 8 / 6). P2.1 / P2.2 between the columns are not connected.
_ON = [  # (pin x, ON index, path, column, J2 pad x)
    (14.01, 1, [(14.01, -9.0), (10.0, -9.0)], 10.0, 9.0),
    (19.09, 2, [(19.09, -8.5), (10.4, -8.5), (9.65, -7.75), (8.0, -7.75)], 8.0, 7.0),
    (21.63, 3, [(21.63, -8.05), (12.6, -8.05), (11.85, -7.3), (6.0, -7.3)], 6.0, 5.0),
]
for x, k, path, col, jx in _ON:
    T(f"ON{k}", 0.25, (x, -10.5), (x, -12.0), layer="F")
    V(f"ON{k}", x, -12.0)
    T(f"ON{k}", 0.25, (x, -12.0), *path, (col, -13.9), (jx + 0.3, -14.6))

# SPI1 SCK: GP10 (top) out past its land -> via just below P2.3 (outside the pad) -> P2.3 (bottom)
T("SPI1_SCK", 0.25, (6.39, -11.0), (6.39, -11.6), (5.0, -13.0), (5.0, -13.75), layer="F")
V("SPI1_SCK", 5.0, -13.75)
T("SPI1_SCK", 0.25, (5.0, -13.75), (5.0, -12.175))

# FLOW_CS: GP26 (top, +y row) out past its land -> via beside P1.8 -> P1.8 (bottom)
T("FLOW_CS", 0.25, (-3.77, 11.0), (-3.77, 12.0), (-4.0, 12.6), layer="F")
V("FLOW_CS", -4.0, 12.6)
T("FLOW_CS", 0.25, (-4.0, 12.6), (-5.0, 12.6), (-5.0, 12.175))
# SPI0_SCK: BMI088 SCK via -> GP6 on top, under the Pico, left of the MOSI path
T("SPI0_SCK", 0.25, (-3.0, 0.0), (-3.0, -2.0), (-6.31, -5.31), (-6.31, -9.0), layer="F")

# SPI1 MOSI / MISO (GP11 / GP12, top) to P2.5 / P2.4 (bottom). On top, under the Pico, MOSI runs at y -7.6 and then
# out between the lands of GP8 / GP9 to a via below P2.5; MISO runs deeper (y -6.9) to a via whose bottom track
# crosses under MOSI to P2.4. GP9 is left spare (boxed in by this route).
T("SPI1_MOSI", 0.25, (8.93, -8.5), (8.93, -7.6), (0.5, -7.6), (0.04, -8.06), (0.04, -12.0), (1.0, -12.96), (1.0, -13.75), layer="F")
V("SPI1_MOSI", 1.0, -13.75)
T("SPI1_MOSI", 0.25, (1.0, -13.75), (1.0, -12.175))
T("SPI1_MISO", 0.25, (11.47, -8.5), (11.47, -6.9), (2.4, -6.9), layer="F")
V("SPI1_MISO", 2.4, -6.9)
T("SPI1_MISO", 0.25, (2.4, -6.9), (3.0, -7.5), (3.0, -9.0))

# GND vias in the four standoff arms (user 2026-11-28): one per arm on its centre line, 3.5 mm from the M2 hole toward
# the board, so the top and bottom pours in each arm are tied together (hole keep-out: 1.1 + 0.25 + 0.3 = 1.65 mm).
for _sx in (1, -1):
    for _sy in (1, -1):
        V("GND", _sx * 22.35, _sy * 14.41)

# GND bridge: the -y strip (J2 GND pins, Pico GND 3/8/13/18 on top) is fenced off from the main pours by the signal
# tracks along both sides of the Pico row; a bottom track from J2.4 up the gap between P2.3 and P2.4 to a via in the
# cavity joins it to the main GND on both layers.
T("GND", 0.3, (3.0, -15.0), (4.0, -14.0), (4.0, -5.6))
V("GND", 4.0, -5.6)
# GND link on top between the BMP390's two GND vias (VSS 3 at the rear side, VSS 8/9 at the front side): drawn before
# the router runs, so I2C cannot climb between them and split the pours into a rear and a front half.
T("GND", 0.3, (-7.05, -1.2), (-4.75, 0.25), layer="F")
# ... and on to the BMI088's GND via under its body, passing above the SCK via at (-3, 0)
T("GND", 0.3, (-4.75, 0.25), (-4.0, 1.4), (-1.0, 1.4), (-0.25, 0.25), layer="F")
