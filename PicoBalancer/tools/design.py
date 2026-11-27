"""
PicoBalancer - single source of truth for the board (stage 2: outline, holes, BOM, netlist).

Board
-----
60 x 200 x 1.6 mm, two 18650 cells in parallel (1S2P) in Keystone 1042P holders, Pico W / Pico 2 W on
2 x 20 female sockets, BNO086 IMU, 2 x MP6550 motor drivers from a TPS61235P 5.1 V boost, BQ25606 USB-C
charger, TPS22810 Pico switch. Design doc: docs/PicoBalancer_Hardware_Design.pdf.

Coordinates
-----------
Geometry sources (both agree, checked 2026-11-27):
* ../Materials/extracted/PicoBalancer_PCB.dxf (Fusion sketch export, mm, y negative: -21 .. -221)
* Fusion 360 model "PicoBalancer_V01 v2", body "PCB" x[-30,30] y[21,221] z[-5.5,-3.9], read only over its MCP
  server (127.0.0.1:27182). Holders / encoders positions below come from that model.
KiCad: origin = board centre (placed at ORIGIN on the sheet), x right, y DOWN, viewed from the holder side
(top). Wheel end (motors) at +y. Fusion -> KiCad: x_k = x_f, y_k = 121 - y_f. DXF -> KiCad: y_k = -(y_dxf + 121).
"""

import uuid

_NS = uuid.UUID("6a1f0c3e-2b4d-4e8f-9a7c-5d3e2f1b0a42")


def uid(name: str) -> str:
    """Deterministic UUID so regenerating yields stable files."""
    return str(uuid.uuid5(_NS, name))


PROJECT = "PicoBalancer"
REVISION = "0.1"
DATE = "2026-11-27"
SHARED_LIBS = "../../Libraries"          # KD_* symbols / footprints, relative to tools/

ORIGIN_X, ORIGIN_Y = 150.0, 105.0        # board centre on the KiCad sheet (A4 297 x 210, board is 200 tall)


def to_kicad(x, y):
    """Board coordinates (centre origin, y down) -> KiCad sheet."""
    return ORIGIN_X + x, ORIGIN_Y + y


# ---------------------------------------------------------------------------
# Mechanics (board coordinates, mm)
# ---------------------------------------------------------------------------
BOARD_W, BOARD_H, BOARD_T = 60.0, 200.0, 1.6
HOLE_D = 2.65                            # DXF circle r 1.325 (M2.5 clearance)
HOLES = [(sx * 26.0, y) for y in (-96.0, 0.0, 96.0) for sx in (-1, 1)]
HOLE_KEEPOUT = 8.0                       # DXF 8 x 8 squares centred on each hole (standoff / washer area)

# Keystone 1042P, positions from the Fusion model (base body x[-29.33,-8.67] y_f[132.67,209.73];
# polarized (+) contact y_f 127.92..136.24, spring (-) contact y_f 203.19..214.48). Mirror for BT2.
# Keystone drawings 1042 rev H (8.12.26) and 1042P rev C (9.28.26): identical mounting pad layout - pads >= 6.47 x 7.46 mm,
# >= 86.80 mm overall (was 86.00 before rev B), locating holes 3.45 and 2.39 mm on a diagonal, 55.20 mm along x 16.00 mm
# across; body 77.05 x 20.65 x 14.86 mm. 1042 bay 64.0 mm (plain cells), 1042P bay 68.9 mm (protected cells).
HOLDER = dict(body=(20.65, 77.05), pad_span_min=86.80, pad_min=(6.47, 7.46), height=14.86,
              holes=((3.45, 2.39), 55.20, 16.00))
# Holder placement (user 2026-11-27): housing outer wall flush with the board's long edges. M2.5 bolts, 5 mm heads:
# head keep-out circle 7.5 mm diameter (r 3.75 mm) around every bolt hole, marked on Dwgs.User and in Fusion. The holder
# position itself is set by HOLDER_TOP_OFFSET (confirmed 11.5 mm), which leaves 7.5 mm from the top hole centres.
# HOLDER_TOP_OFFSET = distance from the PCB top edge (y = -100) to the housing's top end: 11.5 mm, confirmed by the user
# 2026-11-27 (= the minimum that keeps 7.5 mm from the y = -96 holes).
BOLT_HEAD_D = 5.0
BOLT_KEEPOUT_R = 3.75                    # 7.5 mm diameter mark (user 2026-11-27)
HOLDER_TOP_OFFSET = 11.5
_hx = BOARD_W / 2 - HOLDER["body"][0] / 2                                  # 19.675
_hy = -BOARD_H / 2 + HOLDER_TOP_OFFSET + HOLDER["body"][1] / 2             # -49.975 with the default
BT_POS = {"BT1": (-_hx, _hy), "BT2": (_hx, _hy)}   # centre; + contact toward the board centre (+y)

# Pololu 4761 side-entry encoder connectors on the motors (Fusion): x +-6.95..10.70, y_f -4.8..9.4
ENCODER_ZONE = ((6.95, 10.70), (121 - 9.4, 121 + 4.8))     # |x| range, y range (below the board edge at +100)

# Channel between the holders (user layout 2026-11-27): vertical USB-C J5 at its top end, BQ25606 charger
# below it, two battery-clamp holes in its middle (positions to come from the Fusion model, not yet drawn).
HOLDER_CHANNEL = dict(x=(-(_hx - HOLDER["body"][0] / 2), _hx - HOLDER["body"][0] / 2),
                      y=(_hy - HOLDER["pad_span_min"] / 2, _hy + HOLDER["pad_span_min"] / 2))   # x +-9.35
# Battery clamp (user, Fusion "Battery Cover" + 2 holes added to the Fusion PCB body, read 2026-11-27): M2.5 bolts from
# the cover top through Ø2.65 holes at Fusion (0, 182) / (0, 202). The cover touches the PCB only with a central pillar,
# 10 x 30 mm (Fusion x +-5, y 177..207) -> no parts there; traces may pass in the 4.35 mm lanes beside it.
CLAMP_HOLES = [(0.0, -61.0, 2.65), (0.0, -81.0, 2.65)]
COVER_PILLAR = (-5.0, -86.0, 5.0, -56.0)          # x0, y0, x1, y1 (board)

# Bottom-half layout (user, 2026-11-27). Guide rectangles (x0, y0, x1, y1), refined at placement.
ZONES = {
    "Pico W, USB end up": (-10.5, 33.0, 10.5, 84.0),     # centred, micro-USB toward the cells, antenna end down (moved down, user)
    "IMU": (-4.0, 84.0, 4.0, 94.0),                      # centre bottom, closest to the wheel axle (least tilt noise)
    "J3 motor L": (-18.5, 93.0, -9.5, 99.6),            # motor connectors at the bottom edge, left / right
    "J4 motor R": (9.5, 93.0, 18.5, 99.6),
    "U3 driver L": (-27.0, 71.0, -16.0, 79.0),   # up and out to the side (user)           # drivers right above their connectors
    "U4 driver R": (16.0, 71.0, 27.0, 79.0),
    # user 2026-11-27: boost in the bottom part beside the Pico, next to the drivers (left side);
    # slide switch on the other side at the board edge (EG1218 body 11.6 x 4.0, long side along the edge)
    "U5 boost": (-29.0, 44.0, -12.0, 68.0),   # 6 mm higher (user)
    "SW1": (17.55, 29.4, 22.95, 39.2),   # centred between the Pico edge (x 10.5) and the board edge, at the micro-USB height (user)
    "U7 + D2": (17.2, 43.0, 23.3, 58.0),    # below the slide switch (user)
}

PICO_SOCKET_PITCH = 17.78              # 2 x 1x20, 2.54 mm, Pico W / Pico 2 W

# Operating modes (user 2026-11-27): the robot is never driven while charging; it is left disabled (slide switch
# off) to charge slowly. If power is left on, firmware drops MOTOR_EN and BOOST_EN (TPS61235P disconnects 5V1),
# puts the BNO086 to sleep and sends the Pico dormant (wake: RTC or CHG_PG when the adapter is plugged / removed; no user button). The 100 k pull-downs on
# MOTOR_EN / BOOST_EN keep motor power off through resets; the TPS22810 UVLO is the final backstop.

# BNO086 pins (LGA-28) and their SPI-mode connections, from SparkFun VR IMU Breakout BNO086 schematic v10
# (Materials/extracted/sparkfun_bno086/, CC BY-SA 4.0) and the CEVA BNO08X datasheet. SparkFun selects SPI with
# PS0/PS1 solder jumpers to 3V3 (10 k pull-downs) and opens its I2C pull-up jumper; here SPI is fixed: PS1 pulled up,
# PS0/WAKE pulled up and driven by GP22, no I2C pull-ups, no SA0/ADR resistor (H_SA0 is MOSI in SPI mode).
BNO086_PINS = {
    3: ("VDD", "3V3, 100 nF"), 28: ("VDDIO", "3V3, 100 nF"), 2: ("GND", "GND"), 25: ("GNDIO", "GND"),
    10: ("CLKSEL0", "GND (crystal)"), 27: ("XIN32", "Y1 + 22 pF"), 26: ("CLKSEL1/XOUT32", "Y1 + 22 pF"), 9: ("CAP", "100 nF"),
    17: ("H_SA0/MOSI", "SPI1 MOSI GP15"), 20: ("H_SDA/MISO/TX", "SPI1 MISO GP12"), 19: ("H_SCL/SCLK/RX", "SPI1 SCK GP14"),
    18: ("H_CS", "SPI1 CS GP13, 10 k pull-up"), 14: ("H_INT", "IMU_INT GP11"), 11: ("RST", "IMU_RST GP10, 10 k pull-up"),
    6: ("PS0/WAKE", "IMU_WAKE GP22, 10 k pull-up"), 5: ("PS1", "10 k pull-up (SPI)"), 4: ("BOOT", "10 k pull-up, TP1"),
    16: ("S_SDA", "4.7 k pull-up, unused"), 15: ("S_SCL", "4.7 k pull-up, unused"),
}

# ---------------------------------------------------------------------------
# Pin map v2 (Pico W and Pico 2 W, user-approved 2026-11-27), matched to the placement: USB end up, so pins 1-20 run
# down the left side and 21-40 up the right side. GP23/24/25/29 belong to the CYW43439 on both modules.
PINMAP = {
    0: "UART0_TX", 1: "UART0_RX",                      # left, top (debug header J6)
    2: "MOTOR_EN", 3: "BOOST_EN",                      # left; boost sits on the left
    4: "CHG_STAT", 5: "CHG_PG",                        # left, top end
    6: "ENC1_A", 7: "ENC1_B",                          # left encoder (PIO)
    8: "M1_IN1", 9: "M1_IN2",                          # left motor, PWM slice 4 A/B
    10: "IMU_RST", 11: "IMU_INT",                      # left, bottom end
    12: "SPI1_MISO", 13: "SPI1_CS", 14: "SPI1_SCK", 15: "SPI1_MOSI",   # BNO086 on SPI1, bottom-left: nearest the IMU
    16: "ENC2_A", 17: "ENC2_B",                        # right encoder, bottom-right: nearest J4
    18: "SPARE", 19: "USER_LED",                       # right: GP18 spare, D4 user LED
    20: "M2_IN1", 21: "M2_IN2",                        # right motor, PWM slice 2 A/B
    22: "IMU_WAKE",                                    # right
    26: "M1_ISENSE", 27: "M2_ISENSE", 28: "VBAT_SENSE",   # right, the only ADC pins
}

# ---------------------------------------------------------------------------
# BOM lines: (refs, value, symbol, footprint, role). "KD_*" = shared ../../Libraries; names marked
# do not exist yet and are drawn in stage 2 from the datasheets in ../Materials/bom_datasheets.
# Passives rule (root README): R / C 0603, bulk >= 10 uF 0805 or 1206, LEDs 0805.
# ---------------------------------------------------------------------------
_R = "Resistor_SMD:R_0603_1608Metric"
_C = "Capacitor_SMD:C_0603_1608Metric"
_C08 = "Capacitor_SMD:C_0805_2012Metric"
_C12 = "Capacitor_SMD:C_1206_3216Metric"
_LED = "LED_SMD:LED_0805_2012Metric"

BOM = [
    # --- MCU module on sockets ---
    ("U1", "Raspberry Pi Pico W / Pico 2 W", "KD_Modules:RPi_Pico_W_Socket", "KD_Modules:RPi_Pico_Socket_2x20_P2.54mm_Vertical",
     "MCU; the footprint is the two socket rows J1/J2 (2 x 20 pads, rows 17.78 mm)"),
    ("J1 J2", "1x20 female 2.54 mm", "-", "(soldered into the U1 footprint)",
     "Pico sockets, rows 17.78 mm apart; bought parts, no schematic symbol of their own"),
    # --- IMU: BNO086, reference = SparkFun BNO086 breakout (CC BY-SA 4.0) + CEVA BNO08X datasheet ---
    ("U2", "BNO086", "KD_Sensors:BNO086", "KD_Sensors:CEVA_LGA-28_3.8x5.2mm_P0.5mm",
     "9-axis IMU with fusion, SPI1 (PS1 high, PS0/WAKE high at reset)"),
    ("Y1", "32.768kHz 12.5pF", "Device:Crystal", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", "BNO086 XIN32 / XOUT32"),
    ("C1 C2", "22pF 50V", "Device:C", _C, "crystal load (check vs crystal CL)"),
    ("C3 C4 C5", "100nF 16V", "Device:C", _C, "BNO086 VDD, VDDIO, CAP"),
    ("R1 R2", "10k", "Device:R", _R, "BNO086 NRST / BOOTN pull-ups"),
    ("R3 R4", "10k", "Device:R", _R, "BNO086 PS0/WAKE and H_CSN pull-ups (SPI select at reset, CS idle high)"),
    ("R5 R6", "4.7k", "Device:R", _R, "BNO086 S_SDA / S_SCL pull-ups (sensor bus, unused)"),
    ("R7", "10k", "Device:R", _R, "BNO086 PS1 pull-up (SPI mode)"),
    # --- motor drivers: 2 x MP6550 (Pololu 4733 carrier values: 10 uF VIN, 1 uF VCC, 0.47 uF V3P3, 100 pF VISEN) ---
    ("U3 U4", "MP6550GG", "KD_Power:MP6550", "KD_Power:MPS_QFN-12_2x2mm_P0.5mm",
     "H-bridge per motor, 5V1 supply"),
    ("C6 C7", "10uF 16V", "Device:C", _C08, "MP6550 VIN, at the pin"),
    ("C8 C9", "1uF 16V", "Device:C", _C, "MP6550 VCC bypass"),
    ("C10 C11", "0.47uF 16V", "Device:C", _C, "MP6550 V3P3 (LDO unused, nSLEEP_LDO = GND)"),
    # Motor (user, 2026-11-27): Pololu #3072, 30:1 Micro Metal Gearmotor HPCB 6V, extended motor shaft (fits the
    # 4761 encoder). Pololu datasheet rev 6.2 at 6 V: no-load 1100 rpm / 0.13 A, stall 1.5 A (extrapolated), 4.5 kg.mm,
    # max power 1.2 W at 0.82 A -> winding ~4 Ohm; at 5.1 V stall ~1.28 A (1.2 A with the 0.24 Ohm bridge).
    # ILIM = 0.5 V / (100 uA/A x RISET) = 5000 / R -> 4.3 k = 1.16 A: two stalled motors draw 2.33 A, under the
    # 2.49 A boost CC limit, so 5V1 holds; Pololu advises <= 25 % of stall (~0.35 A) continuous - firmware limits that.
    ("R8 R9", "4.3k", "Device:R", _R, "MP6550 ISET: current limit 1.16 A per motor (both stalled 2.33 A < boost 2.49 A)"),
    ("C12 C13", "100pF 50V", "Device:C", _C, "MP6550 VISEN filter (<= 500 pF)"),
    ("R10", "100k", "Device:R", _R, "MOTOR_EN (both nSLEEP_HB) pull-down"),
    # vertical (top-entry) header (user 2026-11-27): JST BM06B-SRSS-TB, body 8.0 x 2.9 x 4.25 mm (catalog p.3)
    ("J3 J4", "JST SH 6-pin vertical (top entry, BM06B-SRSS-G-TB)", "Connector_Generic_MountingPin:Conn_01x06_MountingPin",
     "Connector_JST:JST_SH_BM06B-SRSS-TB_1x06-1MP_P1.00mm_Vertical",
     "motor + encoder (Pololu 4761 pinout: GND, B, A, VCC=3V3, M2, M1)"),
    # user 2026-11-27: also 2 mm spaced solder pads for wiring the motors/encoders directly, pads named on silk
    ("J7 J8", "6 solder pads, 2.0 mm pitch (no part)", "Connector_Generic:Conn_01x06",
     "KD_Connectors:SolderWire_Pads_1x06_P2.00mm_Named",
     "direct-wire alternative to J3/J4, same pinout, silk GND B A VCC M2 M1"),
    # --- 5.1 V boost: TPS61235P (values from Drone_1S_Pico2W, checked against SLVSCK4A) ---
    ("U5", "TPS61235P", "KD_Power:TPS61235P", "KD_Power:Texas_RWL_VQFN-HR-9_2.5x2.5mm_P0.5mm", "5V1 for the motor drivers"),
    ("L2", "1uH, Isat 6.2 A (Wurth 74438357010)", "Device:L", "Inductor_SMD:L_Wuerth_MAPI-4030", "boost inductor"),
    ("C14 C15", "10uF 16V", "Device:C", _C08, "boost input, on BAT (user 2026-11-27)"),
    ("C16 C17 C18", "22uF 10V", "Device:C", _C12, "boost output, >= 20 uF effective at 5.1 V"),
    ("R11", "100k", "Device:R", _R, "BOOST_EN pull-down"),
    ("R12", "49.9k", "Device:R", _R, "boost CC limit 2.49 A"),
    ("C19", "10nF 16V", "Device:C", _C, "CC pin, parallel to R12"),
    # --- charger: BQ25606 + vertical USB-C (values from Drone_1S_Pico2W, checked against SLUSCK6C) ---
    ("J5", "USB-C receptacle vertical (GCT USB4235-03-C)", "Connector:USB_C_Receptacle_USB2.0_16P",
     "KD_Connectors:USB_C_Receptacle_GCT_USB4235_Vertical", "charge input, D+/D- to the charger"),
    ("U6", "BQ25606", "KD_Power:BQ25606",
     "Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm", "1S 3 A charger, power path (thermal vias 0.3 mm added at routing: the stock _ThermalVias variant uses 0.2 mm drills)"),
    ("L1", "1uH, Isat 6.2 A (Wurth 74438357010)", "Device:L", "Inductor_SMD:L_Wuerth_MAPI-4030", "charger buck inductor"),
    ("R13 R14", "5.1k", "Device:R", _R, "USB-C CC1 / CC2 pull-downs"),
    ("R15", "226", "Device:R", _R, "ICHG 3.0 A (1.5 A per cell)"),
    ("R16", "150", "Device:R", _R, "ILIM 3.19 A"),
    ("R17", "5.23k", "Device:R", _R, "TS divider top (0-60 C)"),
    ("R18", "30.9k", "Device:R", _R, "TS divider bottom"),
    ("TH1", "10k NTC 103AT-2", "Device:Thermistor_NTC", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     "cell temperature (DNP: charger temperature left out, user 2026-11-27)"),
    # TS fixed (no NTC): bottom = R18 30.9k || R19 10k = 7.55k, top R17 5.23k -> TS = 0.591 x REGN, inside the BQ25606
    # normal window (between its 10 C and 45 C thresholds) -> charging always allowed, no temperature cut-off.
    ("R19", "10k", "Device:R", _R, "fixed TS resistor in place of TH1 (charger temperature left out)"),
    ("C20", "1uF 25V", "Device:C", _C, "VBUS"),
    ("C21 C22", "10uF 16V", "Device:C", _C08, "PMID"),
    ("C23 C24", "10uF 16V", "Device:C", _C08, "SYS (only load on SYS: <= 20 uF per datasheet)"),
    ("C25", "10uF 16V", "Device:C", _C08, "BAT"),
    ("C26", "4.7uF 10V", "Device:C", _C, "REGN"),
    ("C27", "47nF 16V", "Device:C", _C, "BTST"),
    ("D1", "LED red 0805", "Device:LED", _LED, "STAT charging, from SYS (TI application diagram)"),
    # CHG_STAT (GP4) reads the STAT node through R36: STAT is open drain with D1 pulled up to SYS (<= VBAT + 50 mV, ~4.28 V); with the
    # Pico off (switch off while charging) R36 limits the back-feed through D1 into the unpowered GPIO to < 0.2 mA.
    # Firmware: GP4 input with pull-up (3V3 < SYS - Vf(D1), so D1 stays dark), low = charging.
    ("R36", "10k", "Device:R", _R, "STAT -> CHG_STAT (GP4) series resistor"),
    ("R20", "2.2k", "Device:R", _R, "STAT LED series"),
    # --- Pico switch: TPS22810 + slide switch + back-feed Schottky ---
    ("U7", "TPS22810DBV", "KD_Power:TPS22810DBV", "Package_TO_SOT_SMD:SOT-23-6", "Pico VSYS switch, input BAT (user 2026-11-27), UVLO 2.54 / 2.41 V"),
    # Slide switch (user order 2026-11-27): NKK AS12AP (non-shorting, 3 pins 2.54 mm, body ~9.8 x 5.4 x 9.1 mm + 2.5 mm
    # actuator) or NKK SS12SDP4 (SHORTING make-before-break, 3 pins 2.54 mm, body 6.54 x 4.0 x 4.5 mm). One footprint:
    # 3 pins at 2.54 mm, 0.9 mm holes - also fits the earlier EG1218 (2.50 mm). Common = middle pin -> EN/UVLO (via R21);
    # throws -> BAT through R34 and GND. R34 limits the SS12S make-before-break short of BAT to GND to ~4 mA.
    ("SW1", "SPDT slide (NKK AS12AP; alt. SS12SDP4)", "Switch:SW_SPDT",
     "KD_Switches:SW_Slide_SPDT_3pin_P2.54mm_Vertical", "power switch on EN/UVLO"),
    ("R34", "1k", "Device:R", _R, "slide switch BAT leg: limits the make-before-break short (SS12SDP4) to ~4 mA"),
    ("C28 C29", "1uF 16V", "Device:C", _C, "TPS22810 VIN / VOUT"),
    # UVLO by population (user 2026-11-27, both options on the board). Slide switch common -> R21 -> EN/UVLO:
    #   default  R21 = 0R, R22 / R23 not fitted: internal UVLO 2.54 V on / 2.41 V off.
    #   option   R21 = 156k (switch -> EN), R22 = 100k (EN -> GND), R23 = 1.27M (VOUT -> EN, hysteresis):
    #            3.30 V on / 2.70 V off (checked on Drone_1S_Pico2W against SLVSDH0C). Switch off = EN to GND either way.
    ("R21", "0R (or 156k for the 2.70 V option)", "Device:R", _R, "slide switch -> EN; 156k = divider top for 3.30 / 2.70 V"),
    ("R22 R23", "100k / 1.27M (DNP option)", "Device:R", _R, "EN -> GND / VOUT -> EN, fitted only for the 2.70 V option"),
    # Pico datasheet "Powering Pico": external supply into VSYS through a Schottky, so the Pico's own USB
    # (VBUS -> its Schottky -> VSYS) cannot back-feed the TPS22810 and the cells.
    ("D2", "Schottky 20V 1A (MBR120VLSFT1G)", "Device:D_Schottky", "Diode_SMD:D_SOD-123F",
     "TPS22810 VOUT -> Pico VSYS, blocks USB back-feed"),
    ("R24", "0R (DNP)", "Device:R", _R, "D2 bypass option"),
    ("D3", "LED green 0805", "Device:LED", _LED, "power on (VSYS)"),
    ("R25", "1k", "Device:R", _R, "power LED series"),
    ("R26 R27", "100k", "Device:R", _R, "VBAT_SENSE divider BAT / 2 -> GP28"),
    ("C30", "100nF 16V", "Device:C", _C, "VBAT_SENSE filter"),
    # --- cells, connectors, mechanics ---
    # Default Keystone 1042 (not polarized, for the stock plain cells; user 2026-11-27), alternative 1042P (polarized):
    # identical pad layout in both drawings, so one footprint takes either. With the 1042 a cell can go in backwards
    # -> per-cell protection below.
    ("BT1 BT2", "18650 holder Keystone 1042 (alt. 1042P)", "Device:Battery_Cell",
     "KD_Power:Keystone_1042_1x18650_SMD", "one cell each, in parallel"),
    # --- per-cell reverse-polarity protection (one channel per holder, x = 1 for BT1, 2 for BT2) ---
    # Cells are in parallel, so one shared FET cannot protect them: a reversed cell next to a good one would see
    # 2 x Vcell through the shared node. Each holder gets its own high-side P-FET, and its gate is enabled only by
    # that cell's OWN voltage:
    #   BTx- -> GND.  BTx+ (CELLx) -> Fx (PPTC) -> Qp drain;  Qp source -> BAT (common).  Rgs 100k Qp gate -> source (off).
    #   Qn (DMG2302U) drain -> Qp gate, source -> GND, gate <- CELLx through 10k.  1M CELLx -> GND.
    # Good cell: CELLx > ~1 V -> Qn on -> Qp gate at GND -> Qp on (Vgs = -Vcell, 9.8 mOhm max at -2.5 V);
    #   current both ways, so the charger still charges it.
    # Reversed cell: CELLx = -Vcell -> Qn off (Vgs -4.2 V, within +-8 V) -> Qp Vgs = 0, body diode (drain -> source)
    #   reverse biased: blocks up to 2 x 4.2 V (BVDSS 20 V).
    # Empty holder: 1M holds CELLx at 0 -> Qp off, so the contacts are dead and a cell inserted backwards meets an
    #   FET that is already off. Leakage per good cell: ~4 uA (1M) + 0 (Qn gate).
    # Two good cells at very different voltages still equalize through both FETs; Fx limits that current (trip 5.2 A).
    # Resettable fuse per cell (user 2026-11-27, plain cells): BTx+ -> Fx -> Qp drain. A short on BAT trips both, and
    # Fx also limits the equalizing surge when a mismatched cell goes in. Littelfuse 1812L260TH: Ihold 2.60 A (2.15 A
    # at 50 C), Itrip 5.20 A, 8 V, Imax 100 A, R 15-47 mOhm (R1max after trip). Per-cell load: ~1 A running,
    # 2.2 A worst case (boost at its 2.49 A limit from 3.0 V), 1.5 A charging. Qn senses CELLx at the holder (BTx+).
    # Land pattern per the Littelfuse 1812L datasheet (p.6): two 1.78 x 3.15 mm pads, 3.45 mm gap (7.01 mm overall),
    # larger than KiCad's generic Fuse_1812_4532Metric (1.125 x 3.4, 3.15 gap) - PPTC trip depends on pad heat sinking.
    ("F1 F2", "PPTC 2.6A hold / 5.2A trip 8V (Littelfuse 1812L260TH)", "Device:Polyfuse",
     "KD_Power:Fuse_Littelfuse_1812L",
     "per-cell resettable fuse, BTx+ -> Qp drain"),
    ("Q1 Q2", "DMP2008UFG P-MOSFET 20V 9.8mOhm@-2.5V", "Transistor_FET:DMP3013SFV", "Package_SON:Diodes_PowerDI3333-8",
     "per-cell reverse-polarity switch, BTx+ (drain) -> BAT (source)"),
    ("Q3 Q4", "DMG2302U N-MOSFET 20V Vth<=1V", "Transistor_FET:DMG2302U", "Package_TO_SOT_SMD:SOT-23",
     "turns Qp on only when its own cell is the right way round"),
    ("R28 R29", "100k", "Device:R", _R, "Qp gate -> source (default off)"),
    ("R30 R31", "10k", "Device:R", _R, "Qn gate series from CELLx"),
    ("R32 R33", "1M", "Device:R", _R, "CELLx pull-down: empty holder = Qp off"),
    # user LED (GP19), user-approved 2026-11-27; no user button (user: not needed)
    ("D4", "LED blue 0805", "Device:LED", _LED, "USER_LED (GP19)"),
    ("R35", "1k", "Device:R", _R, "user LED series"),
    ("J6", "1x4 2.54 mm header (DNP)", "Connector_Generic:Conn_01x04",
     "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "UART0 debug: GND, TX, RX, 3V3"),
    ("TP1", "test pad", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", "BNO086 BOOTN"),
]

# ---------------------------------------------------------------------------
# Placement review (stage 0b): sized blocks for the Fusion 360 model (tools/fusion/build_review.py).
# Board coordinates (centre origin, y down, top view). Fusion: x_f = x, y_f = 121 - y, z_f = -3.9 + z (PCB top face).
# (ref, x, y, size_x, size_y, size_z, kind, z0)  - sizes from the datasheets in Materials/; z0 = height of the block's
# bottom above the PCB top. kind sets the colour in Fusion.
# ---------------------------------------------------------------------------
# Holder locating holes (Keystone 1042 / 1042P drawings): diagonal, 16.00 across x 55.20 along, positions from the
# Fusion holder model bosses (16 across, 55.2 along, about the holder centre). Which end takes
# the 3.45 mm hole and which the 2.39 mm hole is TO VERIFY on the part. BT2 holes are for a real holder in the same
# orientation as BT1 (+ end toward the board centre); the Fusion right holder is a mirrored copy, not a buildable part.
# offsets from the holder centre (model bosses): + end (+8 toward the board centre line, +27.6 in y), - end (-8, -27.6)
# Keystone 1042 drawing rev H mounting pad layout (same as KiCad's stock footprint): two 3.45 mm peg holes on the
# 55.20 x 16.00 diagonal and a 2.39 mm hole for the small peg 8.51 mm beyond one 3.45 hole, on the other side, at the
# spring (-) end (KiCad stock model / footprint; TO CHECK on a real holder).
# Offsets from the holder centre (+ end at +y): (+8, +27.62) 3.45, (-8, -27.62) 3.45, (+8, -36.13) 2.39.
HOLDER_HOLES = [(sx + dx, _hy + dy, d) for sx in (-_hx, _hx)
                for dx, dy, d in ((8.0, 27.62, 3.45), (-8.0, -27.62, 3.45), (8.0, -36.13, 2.39))]

REVIEW_PARTS = [
    # top channel between the holders: USB-C + charger
    # (USB-C centred in the space between the board top edge (y -100) and the cover pillar (y -86), user; the charger
    #  below the pillar; VBUS runs down beside the pillar)
    ("J5", 0.0, -93.0, 8.94, 3.16, 6.50, "conn", 0), ("C20", -7.0, -93.0, 1.6, 0.8, 0.8, "cap", 0),
    ("R13", 6.5, -92.0, 1.6, 0.8, 0.5, "res", 0), ("R14", 6.5, -94.0, 1.6, 0.8, 0.5, "res", 0),   # CC1 / CC2 5.1k
    ("U6", 0.0, -48.0, 4.0, 4.0, 0.9, "ic", 0), ("L1", 0.0, -40.0, 4.1, 4.1, 3.1, "ind", 0),
    ("C21", -6.0, -50.0, 2.0, 1.25, 1.25, "cap", 0), ("C22", -6.0, -46.0, 2.0, 1.25, 1.25, "cap", 0),
    ("C23", 6.0, -50.0, 2.0, 1.25, 1.25, "cap", 0), ("C24", 6.0, -46.0, 2.0, 1.25, 1.25, "cap", 0),
    ("C25", 6.0, -40.0, 2.0, 1.25, 1.25, "cap", 0), ("D1", -6.0, -36.0, 2.0, 1.25, 0.8, "led_red", 0),
    # per-cell fuse + reverse FETs, between the holder + ends and the middle holes
    ("F1", -12.0, -5.0, 4.5, 3.2, 0.9, "prot", 0), ("Q1", -12.0, 2.0, 3.3, 3.3, 0.8, "ic", 0),
    ("Q3", -6.5, 2.0, 2.9, 1.3, 1.1, "ic", 0),
    ("F2", 12.0, -5.0, 4.5, 3.2, 0.9, "prot", 0), ("Q2", 12.0, 2.0, 3.3, 3.3, 0.8, "ic", 0),
    ("Q4", 6.5, 2.0, 2.9, 1.3, 1.1, "ic", 0),
    # Pico W on 2 x 1x20 sockets (8.5 mm), micro-USB end up (toward -y), antenna end down
    ("J1", -8.89, 58.5, 2.54, 50.8, 8.5, "socket", 0), ("J2", 8.89, 58.5, 2.54, 50.8, 8.5, "socket", 0),
    ("U1 Pico W", 0.0, 58.5, 21.0, 51.0, 1.0, "pico", 8.5), ("U1 micro-USB", 0.0, 34.3, 7.5, 5.5, 2.7, "metal", 9.5),
    # IMU at the centre bottom, nearest the wheel axle
    ("U2 BNO086", 0.0, 89.0, 3.8, 5.2, 1.1, "ic", 0), ("Y1", 5.0, 89.0, 3.2, 1.5, 0.9, "metal", 0),
    # motor drivers up and out to the sides beside the Pico's lower end (user); vertical connectors at the bottom
    # edge, x +-14 (closer to the encoders; clear of the bolt keep-outs)
    ("U3", -20.0, 75.0, 2.0, 2.0, 0.8, "ic", 0), ("C6", -24.5, 75.0, 2.0, 1.25, 1.25, "cap", 0),
    ("J3", -14.0, 96.8, 8.0, 2.9, 4.25, "conn", 0),
    ("U4", 20.0, 75.0, 2.0, 2.0, 0.8, "ic", 0), ("C7", 24.5, 75.0, 2.0, 1.25, 1.25, "cap", 0),
    ("J4", 14.0, 96.8, 8.0, 2.9, 4.25, "conn", 0),
    # direct-wire solder pad rows (6 pads, 2.0 mm pitch, 3.0 mm long = twice the first draft), above each connector
    ("J7", -14.0, 91.5, 11.5, 3.0, 0.05, "metal", 0), ("J8", 14.0, 91.5, 11.5, 3.0, 0.05, "metal", 0),
    # boost on the left beside the Pico, above the left driver
    ("U5", -20.0, 56.0, 2.5, 2.5, 1.0, "ic", 0), ("L2", -20.0, 64.0, 4.1, 4.1, 3.1, "ind", 0),
    ("C16", -26.5, 50.0, 3.2, 1.6, 1.6, "cap", 0), ("C17", -26.5, 54.0, 3.2, 1.6, 1.6, "cap", 0),
    ("C18", -26.5, 58.0, 3.2, 1.6, 1.6, "cap", 0),
    ("C14", -14.5, 52.0, 2.0, 1.25, 1.25, "cap", 0), ("C15", -14.5, 56.0, 2.0, 1.25, 1.25, "cap", 0),
    # slide switch centred between the Pico edge and the board edge; Pico power path (U7, D2, D3) below it
    ("U7", 20.25, 45.5, 2.9, 2.8, 1.1, "ic", 0), ("D2", 20.25, 50.5, 3.7, 1.6, 1.1, "ic", 0),
    ("SW1", 20.25, 34.3, 5.4, 9.8, 9.1, "switch", 0), ("SW1 actuator", 20.25, 34.3, 2.4, 2.4, 2.5, "white", 9.1),
    ("D3", 20.25, 55.5, 2.0, 1.25, 0.8, "led_green", 0),
    ("D4", 20.25, 62.0, 2.0, 1.25, 0.8, "led_blue", 0),
]

# ---------------------------------------------------------------------------
# Netlist (stage 2). Pin numbers = symbol pin numbers = footprint pad names.
# Sources: BNO086 -> BNO086_PINS; MP6550 datasheet rev 1.0; BQ25606 SLUSCK6C, TPS61235P SLVSCK4A and TPS22810 SLVSDH0C
# as checked on Drone_1S_Pico2W (VSET open = 4.208 V, CE and OTG to GND, VAC = VBUS, FB = VOUT, INACT = AGND, QOD = VOUT,
# CT open); USB-C sink with 5.1 k on CC1 / CC2; Pico W datasheet pinout.
# ---------------------------------------------------------------------------
PICO_GP_PIN = {0: 1, 1: 2, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14, 11: 15, 12: 16, 13: 17, 14: 19,
               15: 20, 16: 21, 17: 22, 18: 24, 19: 25, 20: 26, 21: 27, 22: 29, 26: 31, 27: 32, 28: 34}
PICO_GND = (3, 8, 13, 18, 23, 28, 33, 38)          # 33 = AGND
DNP = {"TH1", "R22", "R23", "R24", "J6"}
VALUES = {"R22": "100k", "R23": "1.27M", "R21": "0R", "Q1": "DMP2008UFG", "Q2": "DMP2008UFG",
          "Q3": "DMG2302U", "Q4": "DMG2302U", "J5": "USB4235-03-C", "U1": "Pico W / Pico 2 W", "SW1": "AS12AP",
          "BT1": "Keystone 1042", "BT2": "Keystone 1042", "F1": "1812L260TH", "F2": "1812L260TH",
          "L1": "1uH 74438357010", "L2": "1uH 74438357010", "Y1": "32.768kHz", "J3": "BM06B-SRSS-G-TB",
          "J4": "BM06B-SRSS-G-TB", "J7": "wire pads", "J8": "wire pads", "J6": "UART (DNP)", "TH1": "103AT-2 (DNP)",
          "U3": "MP6550GG", "U4": "MP6550GG", "U6": "BQ25606", "U7": "TPS22810DBV"}
# U6 VSET (pin 12) MUST stay floating: SLUSCK6C pin table - float (> 50 k to GND) = 4.208 V (4.187-4.229 V), the
# right setting for plain 4.20 V Li-ion 18650s; 5-25 k to GND = 4.400 V and < 500 Ohm (short to GND) = 4.352 V are
# for high-voltage cells and would overcharge these. Layout: no GND pour or via touching pin 12 (stage 3 rule).
NO_CONNECT = {"U1": [24, 30, 35, 37, 40], "U2": [1, 7, 8, 12, 13, 21, 22, 23, 24], "U7": [4], "U6": [2, 12],
              "J5": ["A8", "B8"]}


def build_nets():
    nets = {}

    def add(net, ref, *pins):
        for p in pins:
            nets.setdefault(net, []).append((ref, str(p)))

    # --- Pico W: GPIO per PINMAP (GP18 SPARE left open), supplies ---
    for gp, net in PINMAP.items():
        if net != "SPARE":
            add(net, "U1", PICO_GP_PIN[gp])
    add("GND", "U1", *PICO_GND)
    add("3V3", "U1", 36)
    add("VSYS", "U1", 39)
    # --- BNO086 (SPI) ---
    add("3V3", "U2", 3, 28)
    add("GND", "U2", 2, 25, 10)                          # CLKSEL0 low = 32 kHz crystal
    add("SPI1_MOSI", "U2", 17)
    add("SPI1_MISO", "U2", 20)
    add("SPI1_SCK", "U2", 19)
    add("SPI1_CS", "U2", 18)
    add("IMU_INT", "U2", 14)
    add("IMU_RST", "U2", 11)
    add("IMU_WAKE", "U2", 6)
    add("IMU_PS1", "U2", 5)
    add("IMU_BOOTN", "U2", 4)
    add("IMU_ENV_SDA", "U2", 16)
    add("IMU_ENV_SCL", "U2", 15)
    add("IMU_CAP", "U2", 9)
    add("IMU_XIN", "U2", 27)
    add("IMU_XOUT", "U2", 26)
    add("IMU_XIN", "Y1", 1), add("IMU_XOUT", "Y1", 2)
    add("IMU_XIN", "C1", 1), add("GND", "C1", 2)
    add("IMU_XOUT", "C2", 1), add("GND", "C2", 2)
    for c in ("C3", "C4"):
        add("3V3", c, 1), add("GND", c, 2)
    add("IMU_CAP", "C5", 1), add("GND", "C5", 2)
    for r, net in (("R1", "IMU_RST"), ("R2", "IMU_BOOTN"), ("R3", "IMU_WAKE"), ("R4", "SPI1_CS"), ("R5", "IMU_ENV_SDA"),
                   ("R6", "IMU_ENV_SCL"), ("R7", "IMU_PS1")):
        add("3V3", r, 1), add(net, r, 2)
    add("IMU_BOOTN", "TP1", 1)
    # --- motor drivers: U3 = motor 1 (left, J3), U4 = motor 2 (right, J4) ---
    for k, (u, cvin, cvcc, c33, riset, cvis, j, jw) in enumerate(
            (("U3", "C6", "C8", "C10", "R8", "C12", "J3", "J7"), ("U4", "C7", "C9", "C11", "R9", "C13", "J4", "J8")), 1):
        m = f"M{k}"
        add("5V1", u, 9)
        add("GND", u, 3, 5)                              # nSLEEP_LDO low: internal 3.3 V LDO off
        add(f"{m}_IN1", u, 1), add(f"{m}_IN2", u, 10)
        add("MOTOR_EN", u, 12)
        add(f"{m}_OUT1", u, 2), add(f"{m}_OUT2", u, 8)
        add(f"{m}_ISET", u, 7), add(f"{m}_ISENSE", u, 11)
        add(f"{m}_VCC", u, 6), add(f"{m}_V3P3", u, 4)
        add("5V1", cvin, 1), add("GND", cvin, 2)
        add(f"{m}_VCC", cvcc, 1), add("GND", cvcc, 2)
        add(f"{m}_V3P3", c33, 1), add("GND", c33, 2)
        add(f"{m}_ISET", riset, 1), add("GND", riset, 2)
        add(f"{m}_ISENSE", cvis, 1), add("GND", cvis, 2)
        # connector / wire pads, Pololu 4761 order: 1 GND, 2 B, 3 A, 4 VCC (3V3), 5 M2, 6 M1
        for ref in (j, jw):
            add("GND", ref, 1), add(f"ENC{k}_B", ref, 2), add(f"ENC{k}_A", ref, 3), add("3V3", ref, 4)
            add(f"{m}_OUT2", ref, 5), add(f"{m}_OUT1", ref, 6)
        add("GND", j, "MP")
    add("MOTOR_EN", "R10", 1), add("GND", "R10", 2)
    # --- 5.1 V boost ---
    add("BAT", "U5", 3), add("BOOST_SW", "U5", 2), add("BOOST_EN", "U5", 7)
    add("GND", "U5", 8, 1, 5)                            # INACT unused -> AGND
    add("5V1", "U5", 9, 6)                               # FB to VOUT (fixed 5.1 V part)
    add("BOOST_CC", "U5", 4)
    add("BAT", "L2", 1), add("BOOST_SW", "L2", 2)
    for c in ("C14", "C15"):
        add("BAT", c, 1), add("GND", c, 2)
    for c in ("C16", "C17", "C18"):
        add("5V1", c, 1), add("GND", c, 2)
    add("BOOST_EN", "R11", 1), add("GND", "R11", 2)
    add("BOOST_CC", "R12", 1), add("GND", "R12", 2)
    add("BOOST_CC", "C19", 1), add("GND", "C19", 2)
    # --- USB-C (sink) + BQ25606 ---
    add("VBUS", "J5", "A4", "A9", "B4", "B9")
    add("GND", "J5", "A1", "A12", "B1", "B12", "SH")
    add("USB_CC1", "J5", "A5"), add("USB_CC2", "J5", "B5")
    add("USB_DP", "J5", "A6", "B6"), add("USB_DM", "J5", "A7", "B7")
    add("USB_CC1", "R13", 1), add("GND", "R13", 2)
    add("USB_CC2", "R14", 1), add("GND", "R14", 2)
    add("VBUS", "U6", 24, 1)                             # VAC tied to VBUS
    add("PMID", "U6", 23)
    add("USB_DP", "U6", 3), add("USB_DM", "U6", 4)
    add("CHG_ILIM", "U6", 8), add("CHG_ICHG", "U6", 10)
    add("GND", "U6", 9, 6, 17, 18, 25)                   # /CE low = charge on; OTG must not float
    add("CHG_SW", "U6", 19, 20), add("CHG_BTST", "U6", 21), add("REGN", "U6", 22)
    add("SYS", "U6", 15, 16), add("BAT", "U6", 13, 14)
    add("CHG_TS", "U6", 11), add("CHG_STAT_OD", "U6", 5), add("CHG_PG", "U6", 7)
    add("CHG_SW", "L1", 1), add("SYS", "L1", 2)
    add("CHG_ICHG", "R15", 1), add("GND", "R15", 2)
    add("CHG_ILIM", "R16", 1), add("GND", "R16", 2)
    add("REGN", "R17", 1), add("CHG_TS", "R17", 2)
    for r in ("R18", "R19", "TH1"):
        add("CHG_TS", r, 1), add("GND", r, 2)
    add("VBUS", "C20", 1), add("GND", "C20", 2)
    for c in ("C21", "C22"):
        add("PMID", c, 1), add("GND", c, 2)
    for c in ("C23", "C24"):
        add("SYS", c, 1), add("GND", c, 2)
    add("BAT", "C25", 1), add("GND", "C25", 2)
    add("REGN", "C26", 1), add("GND", "C26", 2)
    add("CHG_BTST", "C27", 1), add("CHG_SW", "C27", 2)
    add("SYS", "R20", 1), add("CHG_LED", "R20", 2)
    add("CHG_LED", "D1", 2), add("CHG_STAT_OD", "D1", 1)     # LED anode 2, cathode 1
    add("CHG_STAT_OD", "R36", 1), add("CHG_STAT", "R36", 2)
    # --- Pico switch: TPS22810, slide switch, UVLO options, Schottky to VSYS ---
    add("BAT", "U7", 1), add("GND", "U7", 2), add("EN_UVLO", "U7", 3), add("VSW", "U7", 6, 5)   # QOD to VOUT
    add("BAT", "C28", 1), add("GND", "C28", 2)
    add("VSW", "C29", 1), add("GND", "C29", 2)
    add("SW_BAT", "SW1", 1), add("SW_COM", "SW1", 2), add("GND", "SW1", 3)
    add("BAT", "R34", 1), add("SW_BAT", "R34", 2)
    add("SW_COM", "R21", 1), add("EN_UVLO", "R21", 2)
    add("EN_UVLO", "R22", 1), add("GND", "R22", 2)
    add("VSW", "R23", 1), add("EN_UVLO", "R23", 2)
    add("VSYS", "D2", 1), add("VSW", "D2", 2)                # cathode 1 -> VSYS
    add("VSW", "R24", 1), add("VSYS", "R24", 2)
    add("VSYS", "R25", 1), add("PWR_LED", "R25", 2)
    add("PWR_LED", "D3", 2), add("GND", "D3", 1)
    add("BAT", "R26", 1), add("VBAT_SENSE", "R26", 2)
    add("VBAT_SENSE", "R27", 1), add("GND", "R27", 2)
    add("VBAT_SENSE", "C30", 1), add("GND", "C30", 2)
    # --- cells: holder -> PPTC -> P-FET (drain) -> BAT (source); N-FET enables the gate from its own cell ---
    for k, (bt, f, qp, qn, rgs, rg, rpd) in enumerate((("BT1", "F1", "Q1", "Q3", "R28", "R30", "R32"),
                                                       ("BT2", "F2", "Q2", "Q4", "R29", "R31", "R33")), 1):
        c = f"CELL{k}"
        add(c, bt, 1), add("GND", bt, 2)
        add(c, f, 1), add(f"{c}_F", f, 2)
        add("BAT", qp, 1, 2, 3), add(f"Q{k}P_G", qp, 4), add(f"{c}_F", qp, 5)
        add(f"Q{k}P_G", qn, 3), add("GND", qn, 2), add(f"Q{k}N_G", qn, 1)     # SOT-23 G 1, S 2, D 3
        add(f"Q{k}P_G", rgs, 1), add("BAT", rgs, 2)
        add(c, rg, 1), add(f"Q{k}N_G", rg, 2)
        add(c, rpd, 1), add("GND", rpd, 2)
    # --- user LED, UART header ---
    add("USER_LED", "R35", 1), add("USER_LED_A", "R35", 2)
    add("USER_LED_A", "D4", 2), add("GND", "D4", 1)
    add("GND", "J6", 1), add("UART0_TX", "J6", 2), add("UART0_RX", "J6", 3), add("3V3", "J6", 4)
    return nets

# ---------------------------------------------------------------------------
# Placement (stage 3, first pass): ref -> (x, y, rotation deg), board coordinates (centre origin, y down, top view),
# all parts on top. Groups follow the reviewed Fusion placement (REVIEW_PARTS); small parts sit next to the pin they
# serve. Rotation 90 = 2-pin parts vertical. Courtyard overlaps are checked by gen_pcb.py (DRC).
# ---------------------------------------------------------------------------
_P = {
    # cells: holders flush with the long edges, + pad at the board-centre end
    "BT1": (BT_POS["BT1"][0], BT_POS["BT1"][1], 0), "BT2": (BT_POS["BT2"][0], BT_POS["BT2"][1], 0),
    # USB-C at the top edge, CC resistors and VBUS cap beside it (channel x +-8.9 between the holder courtyards)
    "J5": (0.0, -93.0, 0), "C20": (-7.5, -93.0, 90), "R13": (7.1, -95.0, 90), "R14": (7.1, -91.4, 90),
    # charger below the cover pillar (y > -56)
    "R15": (-6.0, -29.0, 90), "R16": (-3.0, -29.0, 90), "R17": (0.0, -29.0, 90), "R18": (3.0, -29.0, 90),
    "R19": (6.0, -29.0, 90),
    "U6": (0.0, -47.0, 180), "C21": (4.7, -41.4, 90), "C22": (7.3, -41.4, 90), "C26": (2.8, -41.4, 90),
    "C25": (-6.6, -44.0, 90), "C23": (-4.0, -48.0, 90), "C24": (-6.6, -48.0, 90),
    "L1": (-3.5, -38.5, 0), "C27": (1.0, -41.4, 90), "R36": (0.0, -20.0, 90),
    "D1": (-6.0, -20.0, 90), "R20": (-3.0, -20.0, 90), "TH1": (5.0, -21.3, 0),
    # per-cell fuse + reverse-polarity FETs, below the holder + ends
    "F1": (-14.0, -1.5, 90), "Q1": (-14.0, 6.0, 0), "Q3": (-9.0, 6.0, 0),
    "R28": (-9.5, 2.0, 0), "R30": (-9.5, 10.0, 0), "R32": (-13.5, 10.5, 0),
    "F2": (14.0, -1.5, 90), "Q2": (14.0, 6.0, 0), "Q4": (9.0, 6.0, 0),
    "R29": (9.5, 2.0, 0), "R31": (9.5, 10.0, 0), "R33": (13.5, 10.5, 0),
    # Pico on its sockets, micro-USB end up
    "U1": (0.0, 58.5, 0),
    # left column: UART header, MOTOR_EN pull-down, boost
    "J6": (-22.0, 38.0, 0), "R10": (-14.5, 45.0, 0),
    "U5": (-20.0, 56.0, 0), "L2": (-20.0, 64.0, 0), "C16": (-26.5, 50.0, 0), "C17": (-26.5, 54.0, 0),
    "C18": (-26.5, 58.0, 0), "C14": (-14.5, 52.0, 0), "C15": (-14.5, 56.0, 0), "R11": (-14.5, 59.5, 0),
    "R12": (-20.0, 52.0, 0), "C19": (-20.0, 50.0, 0),
    # right column: slide switch at the micro-USB height, TPS22810 path, VBAT sense, LEDs
    "SW1": (20.25, 34.3, 0), "R34": (15.5, 33.0, 90), "R21": (15.5, 37.5, 90), "R22": (25.5, 33.0, 90),
    "R23": (25.5, 37.5, 90), "U7": (20.25, 45.5, 0), "C28": (15.5, 45.5, 90), "C29": (25.0, 45.5, 90),
    "D2": (20.25, 50.5, 0), "R24": (20.25, 53.0, 0), "R26": (15.5, 56.5, 90), "R27": (15.5, 60.5, 90),
    "C30": (18.5, 60.5, 90), "D3": (24.5, 56.0, 90), "R25": (24.5, 60.0, 90), "D4": (20.25, 68.5, 0),
    "R35": (16.0, 68.5, 0),
    # motor drivers beside the Pico's lower end, wire pads and vertical connectors at the bottom edge
    "U3": (-20.0, 76.0, 0), "C6": (-24.0, 76.0, 90), "C8": (-26.5, 76.0, 90), "C10": (-16.0, 76.0, 90),
    "R8": (-20.0, 80.0, 0), "C12": (-20.0, 72.3, 0),
    "U4": (20.0, 76.0, 0), "C7": (24.0, 76.0, 90), "C9": (26.5, 76.0, 90), "C11": (16.0, 76.0, 90),
    "R9": (20.0, 80.0, 0), "C13": (20.0, 72.3, 0),
    "J7": (-14.0, 91.5, 0), "J8": (14.0, 91.5, 0), "J3": (-14.0, 96.8, 0), "J4": (14.0, 96.8, 0),
    # IMU at the centre bottom
    "U2": (0.0, 89.0, 0), "Y1": (5.0, 89.0, 90), "C1": (3.0, 93.6, 90), "C2": (6.0, 93.6, 90),
    "C3": (-3.0, 93.6, 90), "C4": (-6.0, 93.6, 90), "C5": (0.0, 93.6, 90),
    "R1": (-6.0, 80.0, 90), "R2": (-4.0, 80.0, 90), "R3": (-2.0, 80.0, 90), "R4": (0.0, 80.0, 90), "R7": (2.0, 80.0, 90),
    "R5": (4.0, 80.0, 90), "R6": (6.0, 80.0, 90), "TP1": (-6.5, 87.0, 0),
}
PLACEMENT = _P
