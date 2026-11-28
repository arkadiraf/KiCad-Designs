"""Qwiic deck hand routes (design coordinates, seen from the top), imported by gen_pcb.py deck.

Qwiic J3 is on the bottom (mirrored): pads at x -5.2, y -1.5 GND, -0.5 3V3, +0.5 SDA, +1.5 SCL. Each line runs on
the bottom straight forward, then left (+y) to a via under its socket pin, and up on top to the J1 pad:
SCL -> J1.5 (x 1, outer pad), SDA -> J1.4 (x 3, inner pad), 3V3 -> J1.1 (x 9, outer pad), GND -> J1.10 (x -9).
The topmost Qwiic pin turns first, so nothing crosses. GND is completed by the pours on both layers.
"""
TRACKS, VIAS = [], []


def T(net, w, *pts, layer="B"):
    TRACKS.append((net, layer, w, pts))


def V(net, x, y, d=0.6, drill=0.3):
    VIAS.append((net, x, y, d, drill))


T("I2C_SCL", 0.25, (-5.2, 1.5), (1.0, 1.5), (1.0, 7.7));      V("I2C_SCL", 1.0, 7.7)
T("I2C_SCL", 0.25, (1.0, 7.7), (1.0, 12.6), layer="F")
T("I2C_SDA", 0.25, (-5.2, 0.5), (3.0, 0.5), (3.0, 7.7));      V("I2C_SDA", 3.0, 7.7)
T("I2C_SDA", 0.25, (3.0, 7.7), (3.0, 9.4), layer="F")
T("3V3", 0.4, (-5.2, -0.5), (9.0, -0.5), (9.0, 7.7));         V("3V3", 9.0, 7.7, 0.8, 0.4)
T("3V3", 0.4, (9.0, 7.7), (9.0, 12.6), layer="F")
T("3V3", 0.4, (-2.78, -0.5), (-2.78, -2.0))                    # C1 pad 1
T("GND", 0.4, (-1.22, -2.0), (-1.22, -3.2));                  V("GND", -1.22, -3.2)   # C1 pad 2
T("GND", 0.4, (-5.2, -1.5), (-4.2, -2.5));                    V("GND", -4.2, -2.5)    # Qwiic pin 1
T("GND", 0.4, (-9.0, 9.4), (-9.0, 7.7), layer="F");           V("GND", -9.0, 7.7)     # J1.10
