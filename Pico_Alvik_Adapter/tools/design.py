"""
Pico Alvik Adapter - single source of truth for the design.

Everything that the generator scripts produce (symbol library, footprint
library, schematic, PCB) is derived from the tables in this file, so the
schematic and the board can never disagree.

Coordinate conventions
----------------------
* Board "top view", USB end of both the Pico W and the (replaced) Nano ESP32
  points to the top of the board (smaller Y in KiCad).
* Pico W sits on the TOP side, soldered by its castellated edge pads.
* The Nano-footprint male headers are SMD headers on the BOTTOM side, so the
  top layer under the Pico stays free of through-hole joints.
"""

import uuid

PROJECT = "Pico_Alvik_Adapter"
LIB = "PicoAlvik"          # project-local symbol + footprint library nickname

_NS = uuid.UUID("6f1c1a3e-3a51-4d2e-9a43-5c0b5a1d0001")


def uid(name: str) -> str:
    """Deterministic UUID so regenerating the project yields stable files."""
    return str(uuid.uuid5(_NS, name))


# ---------------------------------------------------------------------------
# Raspberry Pi Pico W pins (physical pin number -> name, electrical type)
# ---------------------------------------------------------------------------
PICO_PINS = {
    1: ("GP0", "bidirectional"),   2: ("GP1", "bidirectional"),
    3: ("GND", "power_in"),        4: ("GP2", "bidirectional"),
    5: ("GP3", "bidirectional"),   6: ("GP4", "bidirectional"),
    7: ("GP5", "bidirectional"),   8: ("GND", "power_in"),
    9: ("GP6", "bidirectional"),   10: ("GP7", "bidirectional"),
    11: ("GP8", "bidirectional"),  12: ("GP9", "bidirectional"),
    13: ("GND", "power_in"),       14: ("GP10", "bidirectional"),
    15: ("GP11", "bidirectional"), 16: ("GP12", "bidirectional"),
    17: ("GP13", "bidirectional"), 18: ("GND", "power_in"),
    19: ("GP14", "bidirectional"), 20: ("GP15", "bidirectional"),
    21: ("GP16", "bidirectional"), 22: ("GP17", "bidirectional"),
    23: ("GND", "power_in"),       24: ("GP18", "bidirectional"),
    25: ("GP19", "bidirectional"), 26: ("GP20", "bidirectional"),
    27: ("GP21", "bidirectional"), 28: ("GND", "power_in"),
    29: ("GP22", "bidirectional"), 30: ("RUN", "input"),
    31: ("GP26_ADC0", "bidirectional"), 32: ("GP27_ADC1", "bidirectional"),
    33: ("AGND", "power_in"),      34: ("GP28_ADC2", "bidirectional"),
    35: ("ADC_VREF", "passive"),   36: ("3V3_OUT", "power_out"),
    37: ("3V3_EN", "input"),       38: ("GND", "power_in"),
    39: ("VSYS", "power_in"),      40: ("VBUS", "passive"),
}

# ---------------------------------------------------------------------------
# Arduino Nano ESP32 header pins (classic Nano numbering 1..30)
# Top view, USB at top:  left column  = 16 (D13) .. 30 (VIN)  top -> bottom
#                        right column = 15 (D12) .. 1 (D1/TX) top -> bottom
# ---------------------------------------------------------------------------
NANO_PINS = {
    1: "D1/TX1", 2: "D0/RX0", 3: "RST", 4: "GND", 5: "D2", 6: "D3", 7: "D4",
    8: "D5", 9: "D6", 10: "D7", 11: "D8", 12: "D9", 13: "D10", 14: "D11",
    15: "D12", 16: "D13", 17: "3V3", 18: "B0", 19: "A0", 20: "A1", 21: "A2",
    22: "A3", 23: "A4", 24: "A5", 25: "A6", 26: "A7", 27: "VBUS", 28: "B1",
    29: "GND", 30: "VIN",
}

# ---------------------------------------------------------------------------
# Signal mapping  Nano pin  ->  Pico pin
#   name, nano_pin, pico_pin, comment
# Alvik usage taken from arduino-alvik-mpy (pinout_definitions.py / uart.py)
# and the Alvik datasheet (AKX00066) block diagram.
# ---------------------------------------------------------------------------
SIGNALS = [
    # net name        Nano  Pico  GPIO  function on the Alvik / Pico peripheral
    # --- pins used by the Alvik (required) ---
    ("D1_TX",         1,    21,   "GP16", "Alvik: UART TX -> STM32 RX | Pico UART0 TX"),
    ("D0_RX",         2,    22,   "GP17", "Alvik: UART RX <- STM32 TX | Pico UART0 RX"),
    ("D2_BOOT0",      5,    26,   "GP20", "Alvik: STM32 BOOT0"),
    ("D3_NRST",       6,    27,   "GP21", "Alvik: STM32 NRST"),
    ("D4_NANO_CHK",   7,    29,   "GP22", "Alvik: NANO_CHK (EXT_CHK)"),
    ("A4_SDA",        23,   9,    "GP6",  "Alvik: I2C SDA (Qwiic/Grove) | Pico I2C1 SDA"),
    ("A5_SCL",        24,   10,   "GP7",  "Alvik: I2C SCL (Qwiic/Grove) | Pico I2C1 SCL"),
    ("A6_ROBOT_CHK",  25,   11,   "GP8",  "Alvik: ROBOT_CHK input"),
    # --- spare Nano pins, not used by the Alvik (bonus, aligned) ---
    ("D5",            8,    31,   "GP26", "Pico ADC0"),
    ("D6",            9,    32,   "GP27", "Pico ADC1"),
    ("D7",            10,   34,   "GP28", "Pico ADC2"),
    ("D13",           16,   2,    "GP1",  ""),
    ("A0",            19,   4,    "GP2",  ""),
    ("A1",            20,   5,    "GP3",  ""),
    ("A2",            21,   6,    "GP4",  ""),
    ("A3",            22,   7,    "GP5",  ""),
    ("A7",            26,   12,   "GP9",  ""),
]

# ---------------------------------------------------------------------------
# Full netlist:  net -> list of (reference, pin)
# ---------------------------------------------------------------------------
def build_nets():
    nets = {}

    def add(net, ref, pin):
        nets.setdefault(net, []).append((ref, str(pin)))

    for name, npin, ppin, _gp, _c in SIGNALS:
        add(name, "J1", npin)
        add(name, "U1", ppin)

    # Ground
    for p in (3, 8, 13, 18, 23, 28, 33, 38):
        add("GND", "U1", p)
    add("GND", "J1", 4)
    add("GND", "J1", 29)
    add("GND", "C1", 2)

    # Power (same as a real Nano ESP32 on the Alvik):
    #   Pico VBUS (USB 5V) -> Nano VBUS/VUSB pin, direct: USB powers/charges the Alvik
    #   Alvik -> Nano VIN -> D1 -> Pico VSYS: Alvik powers the Pico without USB;
    #   D1 stops the Alvik output fighting USB power (fit a 1206 0R instead if safe)
    #   Pico on-board Schottky: VBUS -> VSYS (USB powers the Pico)
    add("VBUS", "U1", 40)
    add("VBUS", "J1", 27)
    add("VIN", "J1", 30)
    add("VIN", "D1", 2)        # anode
    add("VSYS", "D1", 1)       # cathode
    add("VSYS", "U1", 39)
    add("VSYS", "C1", 1)

    # 3V3: Pico 3V3(OUT) -> Nano 3V3 pin (Alvik +3V3_EXT)  JP2 bridged
    add("+3V3", "U1", 36)
    add("+3V3", "JP2", 1)
    add("3V3_NANO", "JP2", 2)
    add("3V3_NANO", "J1", 17)

    # Reset: Nano RST -> Pico RUN, JP3 open (optional)
    add("RUN", "U1", 30)
    add("RUN", "JP3", 1)
    add("NANO_RST", "JP3", 2)
    add("NANO_RST", "J1", 3)

    return nets


def _no_connect():
    used_u = {p for _n, _j, p, _g, _c in SIGNALS} | {3, 8, 13, 18, 23, 28, 33, 38, 30, 36, 39, 40}
    used_j = {j for _n, j, _p, _g, _c in SIGNALS} | {3, 4, 17, 27, 29, 30}
    return {"U1": [p for p in range(1, 41) if p not in used_u],
            "J1": [p for p in range(1, 31) if p not in used_j]}


NO_CONNECT = _no_connect()

POWER_NETS = {"GND", "VSYS", "VIN", "VBUS", "+3V3", "3V3_NANO"}

# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------
COMPONENTS = {
    # ref: (lib_id, value, footprint, extra properties)
    "U1": (f"{LIB}:RPi_Pico_W", "Raspberry Pi Pico W",
           f"{LIB}:RPi_Pico_W_SMD_Castellated", {}),
    "J1": (f"{LIB}:Arduino_Nano_Headers", "Nano footprint headers (2x 1x15 SMD male)",
           f"{LIB}:Arduino_Nano_SMD_Headers_Bottom", {}),
    "D1": ("Device:D_Schottky", "PMEG6020ER (or 1206 0R)",
           "Diode_SMD:Nexperia_CFP3_SOD-123W", {}),
    "C1": ("Device:C", "10uF 10V",
           "Capacitor_SMD:C_0805_2012Metric", {}),
    "JP2": ("Jumper:SolderJumper_2_Bridged", "3V3",
            "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm", {}),
    "JP3": ("Jumper:SolderJumper_2_Open", "RST-RUN",
            "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm", {}),
}

# ---------------------------------------------------------------------------
# Board geometry (mm, KiCad page coordinates)
# ---------------------------------------------------------------------------
BX0, BY0 = 100.0, 100.0          # board top-left corner
BOARD_W, BOARD_H = 24.0, 51.0    # board = Pico length, 1.5 mm wider each side
PICO_C = (BX0 + BOARD_W / 2, BY0 + 25.5)          # Pico centre (USB edge at BY0)
NANO_TOP_PIN_Y = BY0 + 4.14                       # D12/D13 row (USB end)
NANO_C = (BX0 + BOARD_W / 2, NANO_TOP_PIN_Y + 17.78)
# Antenna keep-out notch of the Pico W (14 x 9 mm at the far end)
NOTCH_W, NOTCH_H = 14.0, 9.0
