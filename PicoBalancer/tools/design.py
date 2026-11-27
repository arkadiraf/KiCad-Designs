"""
PicoBalancer - single source of truth for the board (stage 0: outline, holes, BOM).

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
HOLDER = dict(body=(20.7, 77.1), pad_span_min=86.0, pad_min=(6.4, 7.3), height=18.3)
BT_POS = {"BT1": (-19.0, -50.2), "BT2": (19.0, -50.2)}   # centre; + contact toward the board centre (+y)

# Pololu 4761 side-entry encoder connectors on the motors (Fusion): x +-6.95..10.70, y_f -4.8..9.4
ENCODER_ZONE = ((6.95, 10.70), (121 - 9.4, 121 + 4.8))     # |x| range, y range (below the board edge at +100)

# Channel between the holders (user layout 2026-11-27): vertical USB-C J5 at its top end, BQ25606 charger
# below it, two battery-clamp holes in its middle (positions to come from the Fusion model, not yet drawn).
HOLDER_CHANNEL = dict(x=(-8.65, 8.65), y=(-93.5, -6.9))
CLAMP_HOLES = []                         # (x, y, d) - TBD from Fusion

# Bottom-half layout (user, 2026-11-27). Guide rectangles (x0, y0, x1, y1), refined at placement.
ZONES = {
    "Pico W, USB end up": (-10.5, 14.0, 10.5, 65.0),     # centred, micro-USB toward the cells, antenna end down
    "IMU": (-4.0, 84.0, 4.0, 94.0),                      # centre bottom, closest to the wheel axle (least tilt noise)
    "J3 motor L": (-21.0, 93.0, -12.0, 99.6),            # motor connectors at the bottom edge, left / right
    "J4 motor R": (12.0, 93.0, 21.0, 99.6),
    "U3 driver L": (-22.0, 80.0, -11.0, 91.0),           # drivers right above their connectors
    "U4 driver R": (11.0, 80.0, 22.0, 91.0),
    # user 2026-11-27: boost in the bottom part beside the Pico, next to the drivers (left side);
    # slide switch on the other side at the board edge (EG1218 body 11.6 x 4.0, long side along the edge)
    "U5 boost": (-29.0, 50.0, -12.0, 78.0),
    "SW1": (25.4, 30.2, 29.4, 41.8),
    "U7 + D2": (13.0, 26.0, 24.0, 46.0),
}

PICO_SOCKET_PITCH = 17.78              # 2 x 1x20, 2.54 mm, Pico W / Pico 2 W

# Operating modes (user 2026-11-27): the robot is never driven while charging; it is left disabled (slide switch
# off) to charge slowly. If power is left on, firmware drops MOTOR_EN and BOOST_EN (TPS61235P disconnects 5V1),
# puts the BNO086 to sleep and sends the Pico dormant (wake: RTC, GP21 button or CHG_PG). The 100 k pull-downs on
# MOTOR_EN / BOOST_EN keep motor power off through resets; the TPS22810 UVLO is the final backstop.

# ---------------------------------------------------------------------------
# Draft pin map (Pico W and Pico 2 W). GP23/24/25/29 belong to the CYW43439 on both modules.
# ---------------------------------------------------------------------------
PINMAP = {
    0: "UART0_TX", 1: "UART0_RX", 2: "MOTOR_EN", 3: "IMU_WAKE",
    4: "SPI0_MISO", 5: "SPI0_CS", 6: "SPI0_SCK", 7: "SPI0_MOSI",    # BNO086 over SPI0 (RP2040 SPI0 pins)
    8: "IMU_INT", 9: "IMU_RST",
    10: "M1_IN1", 11: "M1_IN2", 12: "M2_IN1", 13: "M2_IN2",
    14: "ENC1_A", 15: "ENC1_B", 16: "ENC2_A", 17: "ENC2_B",
    18: "CHG_STAT", 19: "CHG_PG", 20: "BOOST_EN", 21: "SPARE_BTN", 22: "SPARE_LED",
    26: "M1_ISENSE", 27: "M2_ISENSE", 28: "VBAT_SENSE",
}

# ---------------------------------------------------------------------------
# BOM lines: (refs, value, symbol, footprint, role). "KD_*" = shared ../../Libraries; names marked
# (TO CREATE) do not exist yet and are drawn in stage 2 from the datasheets in ../Materials/bom_datasheets.
# Passives rule (root README): R / C 0603, bulk >= 10 uF 0805 or 1206, LEDs 0805.
# ---------------------------------------------------------------------------
_R = "Resistor_SMD:R_0603_1608Metric"
_C = "Capacitor_SMD:C_0603_1608Metric"
_C08 = "Capacitor_SMD:C_0805_2012Metric"
_C12 = "Capacitor_SMD:C_1206_3216Metric"
_LED = "LED_SMD:LED_0805_2012Metric"

BOM = [
    # --- MCU module on sockets ---
    ("U1", "Raspberry Pi Pico W / Pico 2 W", "KD_Modules:RPi_Pico_2_W", "(module on J1/J2)",
     "MCU; plugs into J1/J2, no footprint of its own"),
    ("J1 J2", "1x20 female 2.54 mm", "Connector_Generic:Conn_01x20",
     "Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical", "Pico sockets, rows 17.78 mm apart"),
    # --- IMU: BNO086, reference = SparkFun BNO086 breakout (CC BY-SA 4.0) + CEVA BNO08X datasheet ---
    ("U2", "BNO086", "KD_Sensors:BNO086 (TO CREATE)", "KD_Sensors:CEVA_LGA-28_3.8x5.2mm_P0.5mm (TO CREATE)",
     "9-axis IMU with fusion, SPI (PS1 high, PS0/WAKE high at reset)"),
    ("Y1", "32.768kHz 12.5pF", "Device:Crystal", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", "BNO086 XIN32 / XOUT32"),
    ("C1 C2", "22pF 50V", "Device:C", _C, "crystal load (check vs crystal CL)"),
    ("C3 C4 C5", "100nF 16V", "Device:C", _C, "BNO086 VDD, VDDIO, CAP"),
    ("R1 R2", "10k", "Device:R", _R, "BNO086 NRST / BOOTN pull-ups"),
    ("R3 R4", "10k", "Device:R", _R, "BNO086 PS0/WAKE and H_CSN pull-ups (SPI select at reset, CS idle high)"),
    ("R5 R6", "4.7k", "Device:R", _R, "BNO086 S_SDA / S_SCL pull-ups (sensor bus, unused)"),
    ("R7", "10k", "Device:R", _R, "BNO086 PS1 pull-up (SPI mode)"),
    # --- motor drivers: 2 x MP6550 (Pololu 4733 carrier values: 10 uF VIN, 1 uF VCC, 0.47 uF V3P3, 100 pF VISEN) ---
    ("U3 U4", "MP6550GG", "KD_Power:MP6550 (TO CREATE)", "KD_Power:MPS_QFN-12_2x2mm_P0.5mm (TO CREATE)",
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
    ("J3 J4", "JST SH 6-pin side entry", "Connector_Generic_MountingPin:Conn_01x06_MountingPin",
     "Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal",
     "motor + encoder (Pololu 4761 pinout: GND, B, A, VCC=3V3, M2, M1)"),
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
     "KD_Connectors:USB_C_Receptacle_GCT_USB4235_Vertical (TO CREATE)", "charge input, D+/D- to the charger"),
    ("U6", "BQ25606", "KD_Power:BQ25606",
     "Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias", "1S 3 A charger, power path"),
    ("L1", "1uH, Isat 6.2 A (Wurth 74438357010)", "Device:L", "Inductor_SMD:L_Wuerth_MAPI-4030", "charger buck inductor"),
    ("R13 R14", "5.1k", "Device:R", _R, "USB-C CC1 / CC2 pull-downs"),
    ("R15", "226", "Device:R", _R, "ICHG 3.0 A (1.5 A per cell)"),
    ("R16", "150", "Device:R", _R, "ILIM 3.19 A"),
    ("R17", "5.23k", "Device:R", _R, "TS divider top (0-60 C)"),
    ("R18", "30.9k", "Device:R", _R, "TS divider bottom"),
    ("TH1", "10k NTC 103AT-2", "Device:Thermistor_NTC", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     "cell temperature, taped between the cells"),
    ("R19", "10k (DNP option)", "Device:R", _R, "fixed TS resistor in place of TH1 (no temperature cut-off)"),
    ("C20", "1uF 25V", "Device:C", _C, "VBUS"),
    ("C21 C22", "10uF 16V", "Device:C", _C08, "PMID"),
    ("C23 C24", "10uF 16V", "Device:C", _C08, "SYS (only load on SYS: <= 20 uF per datasheet)"),
    ("C25", "10uF 16V", "Device:C", _C08, "BAT"),
    ("C26", "4.7uF 10V", "Device:C", _C, "REGN"),
    ("C27", "47nF 16V", "Device:C", _C, "BTST"),
    ("D1", "LED red 0805", "Device:LED", _LED, "STAT charging"),
    ("R20", "2.2k", "Device:R", _R, "STAT LED series"),
    # --- Pico switch: TPS22810 + slide switch + back-feed Schottky ---
    ("U7", "TPS22810DBV", "KD_Power:TPS22810DBV", "Package_TO_SOT_SMD:SOT-23-6", "Pico VSYS switch, input BAT (user 2026-11-27), UVLO 2.54 / 2.41 V"),
    # E-Switch EG1218 (Digi-Key EG1903-ND, user pick): SPDT, top actuator, through hole, 0.2 A / 30 VDC,
    # 3 pins 2.50 mm pitch, 0.90 mm holes, body 11.6 x 4.0 x 5.4 mm + 2.0 mm actuator, 2.5 mm travel
    # (drawing P040040 rev C). Common = pin 2 (middle). Carries the EN/UVLO signal only (uA).
    ("SW1", "SPDT slide (E-Switch EG1218)", "Switch:SW_SPDT",
     "KD_Switches:SW_E-Switch_EG1218_SPDT_Vertical (TO CREATE)", "power switch on EN/UVLO"),
    ("C28 C29", "1uF 16V", "Device:C", _C, "TPS22810 VIN / VOUT"),
    ("R21 R22 R23", "156k / 100k / 1.27M (DNP option)", "Device:R", _R,
     "3.30 / 2.70 V UVLO divider option; not fitted: internal 2.54 / 2.41 V kept (user 2026-11-27)"),
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
    # Keystone 1042P (polarized) or 1042 (plain leaf springs, NOT polarized): same SMT pad layout on the catalog page,
    # so one footprint takes either. With the 1042 a cell can go in backwards -> per-cell protection below.
    ("BT1 BT2", "18650 holder Keystone 1042P (alt. 1042)", "Device:Battery_Cell",
     "KD_Power:Keystone_1042_1x18650_SMD (TO CREATE)", "one cell each, in parallel"),
    # --- per-cell reverse-polarity protection (one channel per holder, x = 1 for BT1, 2 for BT2) ---
    # Cells are in parallel, so one shared FET cannot protect them: a reversed cell next to a good one would see
    # 2 x Vcell through the shared node. Each holder gets its own high-side P-FET, and its gate is enabled only by
    # that cell's OWN voltage:
    #   BTx- -> GND.  BTx+ (CELLx) -> Qp drain;  Qp source -> BAT (common).  Rgs 100k Qp gate -> source (off).
    #   Qn (DMG2302U) drain -> Qp gate, source -> GND, gate <- CELLx through 10k.  1M CELLx -> GND.
    # Good cell: CELLx > ~1 V -> Qn on -> Qp gate at GND -> Qp on (Vgs = -Vcell, 9.8 mOhm max at -2.5 V);
    #   current both ways, so the charger still charges it.
    # Reversed cell: CELLx = -Vcell -> Qn off (Vgs -4.2 V, within +-8 V) -> Qp Vgs = 0, body diode (drain -> source)
    #   reverse biased: blocks up to 2 x 4.2 V (BVDSS 20 V).
    # Empty holder: 1M holds CELLx at 0 -> Qp off, so the contacts are dead and a cell inserted backwards meets an
    #   FET that is already off. Leakage per good cell: ~4 uA (1M) + 0 (Qn gate).
    # Not covered: two good cells at very different voltages still equalize through both FETs (insert matched cells).
    ("Q1 Q2", "DMP2008UFG P-MOSFET 20V 9.8mOhm@-2.5V", "Device:Q_PMOS", "Package_SON:Diodes_PowerDI3333-8",
     "per-cell reverse-polarity switch, BTx+ (drain) -> BAT (source)"),
    ("Q3 Q4", "DMG2302U N-MOSFET 20V Vth<=1V", "Device:Q_NMOS", "Package_TO_SOT_SMD:SOT-23",
     "turns Qp on only when its own cell is the right way round"),
    ("R28 R29", "100k", "Device:R", _R, "Qp gate -> source (default off)"),
    ("R30 R31", "10k", "Device:R", _R, "Qn gate series from CELLx"),
    ("R32 R33", "1M", "Device:R", _R, "CELLx pull-down: empty holder = Qp off"),
    ("J6", "1x4 2.54 mm header (DNP)", "Connector_Generic:Conn_01x04",
     "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "UART0 debug: GND, TX, RX, 3V3"),
    ("TP1", "test pad", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", "BNO086 BOOTN"),
]
