#!/usr/bin/env python3
"""Flight controller (FC) electrical design: Pico 2 W pin map, parts with symbols, netlist.

Stage 2/3 for the FC module (2026-11-28). The placement lives in design.FC (sensors, passives, connectors),
the board-to-board pinout in design.B2B_J1 / B2B_J2 (shared with the frame). Pin numbers = symbol pin
numbers = footprint pad names.

Sources:
  * Pico 2 W: RPi_Pico_2_W_datasheet.pdf (pinout; GP23/24/25/29 belong to the CYW43439 and are not on pins).
  * BMI088: BST-BMI088-DS001 rev 1.9 table 14, SPI mode (PS = GND), SDO1 + SDO2 tied (one MISO), unused INT2 /
    INT4 left open ("DNC"); reference circuit Crazyflie Bolt 1.1 rev H (100 nF, 1 uH + 4.7 uF supply filter).
  * BMP390: BST-BMP390-DS002 rev 1.7 table 52, I2C mode (CSB high), SDO high = address 0x77 (as the Bolt).
  * Flow deck v2 rev A schematic: VCC (left 1) = 3V3, VCOM (right 9) = VSYS, I2C on left 4/5, PMW3901 SPI on
    right 3-5 with CS on IO_3 (left 8), GND left 10.
  * RP2350 function table: SPI0 RX GP4 / SCK GP6 / TX GP7, SPI1 SCK GP10 / TX GP11 / RX GP12, I2C0 SDA GP20 /
    SCL GP21; DShot on PIO (any pins, GP16-19 consecutive).
"""
from design import B2B_J1, B2B_J2, REVISION, DATE  # noqa: F401  (re-exported for gen_schematic)

PROJECT = "Drone_1S_FC"

# ---------------------------------------------------------------------------
# Pico 2 W pin map (user-approved buses, 2026-11-28). 24 of the 26 free GPIOs used; GP0 and GP9 spare.
# Right row (pins 1-20, -y side) carries the IMU and the Flow deck SPI and the motor-switch lines to J2;
# left row (pins 21-40, +y side) carries DShot, I2C and the J1 lines.
# ---------------------------------------------------------------------------
PINMAP = {
    0: "SPARE",
    1: "MOTOR_PG",          # J2.6: wired-AND of the four TPS22997 PG outputs (frame), 47k pull-up R7
    2: "ON4",               # J2.5
    3: "IMU_INT_GYR",       # BMI088 INT3 (gyro data ready)
    4: "SPI0_MISO",         # BMI088 SDO1 + SDO2
    5: "IMU_CS_ACC",        # BMI088 CSB1
    6: "SPI0_SCK",          # BMI088 SCK
    7: "SPI0_MOSI",         # BMI088 SDI
    8: "IMU_INT_ACC",       # BMI088 INT1 (accel data ready)
    9: "SPARE",             # (was IMU_CS_GYR: boxed in by the SPI1 MOSI route, 2026-11-28)
    10: "SPI1_SCK",         # Flow deck right 3 (PMW3901)
    11: "SPI1_MOSI",        # Flow deck right 5
    12: "SPI1_MISO",        # Flow deck right 4
    13: "ON1",              # J2.1  (GP13..15 nest through the P2 pad gaps to J2.1..3 without crossing)
    14: "ON2",              # J2.2
    15: "ON3",              # J2.3
    16: "DSHOT4_MCU",       # -> R6 100R -> J1.4   (order reversed so the four paths nest without crossing;
    17: "DSHOT3_MCU",       # -> R5 -> J1.3          firmware maps the PIO pins to motors)
    18: "DSHOT2_MCU",       # -> R4 -> J1.2
    19: "DSHOT1_MCU",       # -> R3 -> J1.1
    20: "I2C_SDA",          # BMP390 + Flow deck left 4 (VL53L1X), 4.7k pull-up R1
    21: "I2C_SCL",          # BMP390 + Flow deck left 5, 4.7k pull-up R2
    22: "BOOST_EN",         # J1.6 (100k pull-down on the frame)
    26: "FLOW_CS",          # Flow deck left 8 = IO_3 (PMW3901 CS)
    27: "CHG_PG",           # J1.7 (BQ25606 PG, open drain, pulled up on the frame side)
    28: "IMU_CS_GYR",       # BMI088 CSB2 (its escape via is on the +y side, next to this pin row)
}
PICO_GP_PIN = {0: 1, 1: 2, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14, 11: 15, 12: 16, 13: 17, 14: 19,
               15: 20, 16: 21, 17: 22, 18: 24, 19: 25, 20: 26, 21: 27, 22: 29, 26: 31, 27: 32, 28: 34}
PICO_GND = (3, 8, 13, 18, 23, 28, 33, 38)          # 33 = AGND

# Flow deck pin use (DECK_LEFT / DECK_RIGHT in design.py; pin 1 at the front)
DECK_P1 = {1: "3V3", 4: "I2C_SDA", 5: "I2C_SCL", 8: "FLOW_CS", 10: "GND"}
DECK_P2 = {3: "SPI1_SCK", 4: "SPI1_MISO", 5: "SPI1_MOSI", 9: "VSYS"}

# ---------------------------------------------------------------------------
# Parts: (refs, value, symbol, footprint, role)
# ---------------------------------------------------------------------------
_R = "Resistor_SMD:R_0603_1608Metric"
_C = "Capacitor_SMD:C_0603_1608Metric"
BOM = [
    ("U1", "Raspberry Pi Pico 2 W", "KD_Modules:RPi_Pico_2_W", "KD_Modules:RPi_Pico_2_W_SMD_Castellated",
     "MCU, castellated SMD on the FC top; underside TP2/TP3 (USB), TP6 (BOOTSEL), SWD pads used"),
    ("U2", "BMI088", "KD_Sensors:BMI088", "KD_Sensors:Bosch_LGA-16_3x4.5mm_P0.5mm", "IMU on SPI0, bottom centre"),
    ("U3", "BMP390", "KD_Sensors:BMP390", "KD_Sensors:Bosch_LGA-10_2x2mm_P0.5mm", "barometer on I2C0, 0x77"),
    ("C1", "100nF", "Device:C", _C, "BMI088 decoupling"),
    ("C2", "100nF", "Device:C", _C, "BMP390 decoupling"),
    ("L1", "1uH", "Device:L", "Inductor_SMD:L_0603_1608Metric", "sensor supply filter 3V3 -> 3V3_SENS (Bolt: MLZ1608)"),
    ("C3", "4.7uF", "Device:C", _C, "3V3_SENS bulk (filter)"),
    ("R1 R2", "4.7k", "Device:R", _R, "I2C0 SDA / SCL pull-ups to 3V3"),
    ("R3 R4 R5 R6", "100", "Device:R", _R, "DShot series resistors at the Pico (Bolt)"),
    ("R7", "47k", "Device:R", _R, "MOTOR_PG pull-up to 3V3"),
    ("J1 J2", "Wurth 62001011121", "Connector_Generic:Conn_01x10",
     "Connector_PinHeader_2.00mm:PinHeader_1x10_P2.00mm_Vertical", "board-to-board male headers to the frame J5 / J6"),
    ("P1 P2", "TMM-110-01-T-S-SM-P", "Connector_Generic:Conn_01x10",
     "Connector_PinHeader_2.00mm:PinHeader_1x10_P2.00mm_Vertical_SMD_Pin1Left", "Flow deck v2 headers (posts trimmed)"),
    ("J9", "SM03B-SRSS-TB (DNP)", "Connector_Generic_MountingPin:Conn_01x03_MountingPin",
     "Connector_JST:JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal", "SWD: SWCLK, GND, SWDIO (not fitted)"),
    ("SW1", "B3U-1000PM-B", "Switch:SW_Push", "Button_Switch_SMD:SW_SPST_B3U-1000P-B", "BOOTSEL (Pico TP6 to GND)"),
]
DNP = {"J9"}
VALUES = {"U1": "Pico 2 W", "J1": "62001011121", "J2": "62001011121", "P1": "TMM-110-01-T-S-SM-P",
          "P2": "TMM-110-01-T-S-SM-P", "J9": "SM03B-SRSS-TB", "SW1": "B3U-1000PM-B"}
NO_CONNECT = {
    "U1": [1, 12, 30, 35, 37, 40],             # GP0, GP9 spare; RUN, ADC_VREF, 3V3_EN open; VBUS unused (USB host side)
    "U2": [1, 13],                              # INT2, INT4 (DNC)
    "U3": [7],                                  # INT
    "P1": [2, 3, 6, 7, 9],
    "P2": [1, 2, 6, 7, 8, 10],
    "J9": ["MP"],
}


def build_nets():
    nets = {}

    def add(net, ref, *pins):
        for p in pins:
            nets.setdefault(net, []).append((ref, str(p)))

    # --- Pico 2 W ---
    for gp, net in PINMAP.items():
        if net != "SPARE":
            add(net, "U1", PICO_GP_PIN[gp])
    add("GND", "U1", *PICO_GND, "TP1", "SWD_GND")
    add("3V3", "U1", 36)
    add("VSYS", "U1", 39)
    add("USB_DM", "U1", "TP2"), add("USB_DP", "U1", "TP3")
    add("BOOTSEL", "U1", "TP6")
    add("SWCLK", "U1", "SWCLK"), add("SWDIO", "U1", "SWDIO")
    # --- BMI088 (SPI) ---
    add("3V3_SENS", "U2", 3, 11)
    add("GND", "U2", 2, 4, 6, 7)                 # pin 2 NC -> GND (Bosch), PS = GND selects SPI
    add("SPI0_SCK", "U2", 8), add("SPI0_MOSI", "U2", 9), add("SPI0_MISO", "U2", 10, 15)
    add("IMU_CS_ACC", "U2", 14), add("IMU_CS_GYR", "U2", 5)
    add("IMU_INT_ACC", "U2", 16), add("IMU_INT_GYR", "U2", 12)
    add("3V3_SENS", "C1", 1), add("GND", "C1", 2)
    # --- BMP390 (I2C, 0x77) ---
    add("3V3_SENS", "U3", 1, 10, 5, 6)          # VDDIO, VDD, SDO (address 0x77), CSB (I2C)
    add("GND", "U3", 3, 8, 9)
    add("I2C_SCL", "U3", 2), add("I2C_SDA", "U3", 4)
    add("3V3_SENS", "C2", 1), add("GND", "C2", 2)
    # --- sensor supply filter ---
    add("3V3", "L1", 1), add("3V3_SENS", "L1", 2)
    add("3V3_SENS", "C3", 1), add("GND", "C3", 2)
    # --- pull-ups ---
    add("3V3", "R1", 1), add("I2C_SDA", "R1", 2)
    add("3V3", "R2", 1), add("I2C_SCL", "R2", 2)
    add("3V3", "R7", 1), add("MOTOR_PG", "R7", 2)
    # --- DShot series resistors ---
    for k, r in enumerate(("R3", "R4", "R5", "R6"), 1):
        add(f"DSHOT{k}_MCU", r, 1), add(f"DSHOT{k}", r, 2)
    # --- board-to-board headers ---
    for ref, sig in (("J1", B2B_J1), ("J2", B2B_J2)):
        for k, net in enumerate(sig, 1):
            add(net, ref, k)
    # --- Flow deck ---
    for ref, m in (("P1", DECK_P1), ("P2", DECK_P2)):
        for k, net in m.items():
            add(net, ref, k)
    # --- SWD (J9, DNP) and BOOTSEL button ---
    add("SWCLK", "J9", 1), add("GND", "J9", 2), add("SWDIO", "J9", 3)
    add("BOOTSEL", "SW1", 1), add("GND", "SW1", 2)
    return nets


POWER_NETS = {"VSYS", "3V3", "GND"}


if __name__ == "__main__":
    n = build_nets()
    used = sorted(gp for gp, v in PINMAP.items() if v != "SPARE")
    print(f"{len(n)} nets, {sum(len(v) for v in n.values())} connections; GPIOs used {len(used)}, spare "
          f"{[gp for gp, v in PINMAP.items() if v == 'SPARE']}")
    single = {k: v for k, v in n.items() if len(v) < 2}
    print("single-pin nets:", single or "none")
