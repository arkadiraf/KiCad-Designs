#!/usr/bin/env python3
"""Qwiic deck: a Crazyflie-deck-format adapter that plugs into the FC's Flow deck headers (P1 / P2) in place of the
Flow deck v2, and brings the deck I2C bus out on a SparkFun Qwiic connector (user, 2026-11-28).

* Outline = Flow deck v2 (21.079 x 27.94 mm, Bitcraze drawing), centred on the deck axis; rows 22.0 mm apart,
  pin 1 at the FRONT, same scad frame as the FC (x forward, y left), seen from the TOP.
* Sockets J1 (left, +y) / J2 (right, -y): Sullins NPPN101BFLD-RC 1x10 2.00 mm SMD, on the deck TOP, like the Flow
  deck's own sockets. Their contact point is 2.5 mm deep, so the FC's P1 / P2 posts must stay at the full 3.20 mm
  (not trimmed to 1.9 mm as for the Flow deck) on any FC that takes this adapter.
* Qwiic J3: JST SH 4-pin right-angle SM04B-SRSS-TB on the BOTTOM at the rear edge, opening backwards (mirrored there,
  its pins reach the socket pins without crossing; and the cable plugs in from below). SparkFun Qwiic
  pinout: 1 GND, 2 3.3V, 3 SDA, 4 SCL. Bus from the deck pins: VCC_3V (left 1) = FC 3V3, SDA left 4, SCL left 5,
  GND left 10. The FC already pulls SDA / SCL up (4.7k), so the deck adds none; C1 decouples the Qwiic supply.
* Also fits a real Crazyflie (same deck pinout, VCC 3.0 V there) - the Qwiic device must accept 3.0 V then.
"""
from design import DATE, REVISION  # noqa: F401

PROJECT = "Drone_1S_QwiicDeck"
TITLE = "1S Pico 2 W drone - Qwiic deck (Flow deck replacement)"
OUTLINE = (21.079, 28.4)               # Flow deck v2 is 21.079 x 27.94; +0.46 in y so the socket pads keep 0.4 mm to the edge
FILLET = 1.0
ROW_Y = 11.0                           # deck rows at y = +-11 (22.0 mm apart)
THICKNESS = 1.6                        # OSH Park prototype (0.8 mm later)
QWIIC_POS = (-7.2, 0.0)                # footprint origin, BOTTOM; opening toward the rear edge (x = -10.54), MP pads 0.46 mm in
C1_POS = (-2.0, -2.0)                  # 3V3 decoupling, bottom, under the Qwiic 3V3 line

DECK_P1 = {1: "3V3", 4: "I2C_SDA", 5: "I2C_SCL", 10: "GND"}   # left row (Crazyflie VCC_3V, SDA, SCL, GND)

_C = "Capacitor_SMD:C_0603_1608Metric"
BOM = [
    ("J1 J2", "Sullins NPPN101BFLD-RC", "Connector_Generic:Conn_01x10",
     "KD_Connectors:Sullins_NPPN101BFLD_1x10_P2.00mm_SMD", "deck sockets onto the FC's P1 / P2 (posts untrimmed)"),
    ("J3", "Qwiic SM04B-SRSS-TB", "Connector_Generic_MountingPin:Conn_01x04_MountingPin",
     "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal", "SparkFun Qwiic: GND, 3.3V, SDA, SCL"),
    ("C1", "1uF", "Device:C", _C, "Qwiic 3V3 decoupling"),
]
DNP = set()
VALUES = {"J1": "NPPN101BFLD-RC", "J2": "NPPN101BFLD-RC", "J3": "SM04B-SRSS-TB"}
NO_CONNECT = {"J1": [2, 3, 6, 7, 8, 9], "J2": list(range(1, 11))}
PINMAP = {}                            # no MCU on this board


def build_nets():
    nets = {}

    def add(net, ref, *pins):
        for p in pins:
            nets.setdefault(net, []).append((ref, str(p)))
    for k, net in DECK_P1.items():
        add(net, "J1", k)
    add("GND", "J3", 1, "MP"), add("3V3", "J3", 2), add("I2C_SDA", "J3", 3), add("I2C_SCL", "J3", 4)
    add("3V3", "C1", 1), add("GND", "C1", 2)
    return nets


POWER_NETS = {"3V3", "GND"}

# schematic layout for gen_schematic.py
SCH = dict(
    out=("QwiicDeck", PROJECT),
    title=TITLE,
    comment="Crazyflie-deck adapter: FC deck I2C (left row 1 / 4 / 5 / 10) -> SparkFun Qwiic J3",
    blocks=[
        ("Deck sockets (Sullins NPPN101BFLD-RC) onto the FC P1 (left) / P2 (right); pin 1 at the front", 20, 30, 220,
         ["J1", "J2"]),
        ("Qwiic (SparkFun pinout: 1 GND, 2 3.3V, 3 SDA, 4 SCL); pull-ups are on the FC (4.7k)", 260, 30, 120, ["J3", "C1"]),
    ],
    flags=("GND", "3V3"),
    notes=[("Power flags: 3V3 and GND come from the FC through the deck connector (left 1 / left 10).", 20, 150, 1.5),
           ("FC P1 / P2 posts must stay at 3.20 mm (untrimmed) to reach the Sullins contacts (2.5 mm deep).", 20, 158, 1.5)],
)
