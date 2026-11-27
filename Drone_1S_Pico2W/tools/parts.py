"""Orderable parts (manufacturer part numbers) for both boards, Digi-Key / Mouser stock lines.

Distributor sites are blocked from the build container, so these MPNs were chosen from the
manufacturers' standard series and are NOT yet checked for stock or price. Upload
fabrication/BOM_DigiKey.csv to the Digi-Key BOM Manager (or Mouser's BOM tool), which maps each
MPN to its distributor part number, price and stock, and flags any that don't resolve.

status: "ok"      standard part, value fixed by the design doc
        "verify"  MPN or exact variant to confirm on Digi-Key / Mouser
        "TBD"     value waits for a datasheet (see Materials/MISSING_DATASHEETS.md) or a decision
        "DNP"     footprint only, not fitted by default
The Bitcraze Flow deck v2 is ordered from Bitcraze directly and is not listed.
"""

YAGEO = "Yageo"
MURATA = "Murata"
TI = "Texas Instruments"

# key = the refs string of a design.FRAME_BOM line (frame) or the refs below (FC / mechanical)
# value = (manufacturer, MPN, status, note)
FRAME_MPN = {
    "J10": ("GCT", "USB4105-GF-A", "ok", "USB-C receptacle, USB 2.0, 16P top mount"),
    "U1": (TI, "BQ25606RGER", "ok", ""),
    "L1": ("Wurth Elektronik", "74438357010", "ok", "WE-MAPI 4030, 1 uH, Isat 6.2 A, 3.1 mm tall; replaces XAL4020-102MEC (in stock)"),
    "R1 R2": (YAGEO, "RC0603FR-075K1L", "ok", ""),
    "R3": (YAGEO, "RC0603FR-07226RL", "ok", ""),
    "R4": (YAGEO, "RC0603FR-07150RL", "ok", ""),
    "R5": (YAGEO, "RC0603FR-075K23L", "ok", "BQ25606 datasheet 9.3.5"),
    "R6": (YAGEO, "RC0603FR-0730K9L", "ok", "BQ25606 datasheet 9.3.5"),
    "TH1": ("Semitec", "103AT-2", "ok", "10 k +-1 %, B 3435 K +-1 %, radial 2.54 mm"),
    "C1": ("Samsung", "CL10B105KA8NNNC", "verify", "1 uF 25 V X7R 0603"),
    "C2 C23": (MURATA, "GRM21BR61C106KE15L", "ok", "10 uF 16 V X5R 0805"),
    "C3 C4": (MURATA, "GRM21BR61C106KE15L", "ok", "16 V part on the 10 V lines: less DC-bias loss"),
    "C5": (MURATA, "GRM21BR61C106KE15L", "ok", ""),
    "C6": (MURATA, "GRM188R61A475KE15D", "ok", "4.7 uF 10 V X5R 0603"),
    "C7": (MURATA, "GRM188R71H473KA61D", "ok", "47 nF 50 V X7R 0603"),
    "D1": ("Lite-On", "LTST-C171KRKT", "verify", "red 0805 (LEDs are 0805 in this repo)"),
    "R7": (YAGEO, "RC0603FR-072K2L", "ok", ""),
    "U2": (TI, "TPS22810DBVR", "ok", "SOT-23-6 (DBV)"),
    "SW1": ("APEM", "MA12RTR", "ok", "replaces PCM12SMTR (last-time buy); same PCM12 land pattern"),
    "C8 C9": (MURATA, "GRM188R71C105KA12D", "ok", "1 uF 16 V X7R 0603"),
    "R8 R9 R10": (YAGEO, "RC0603FR-07156KL / -07100KL / -071M27L", "DNP", "UVLO divider option"),
    "U3 U4 U5 U6": (TI, "TPS22997RYZR", "ok", ""),
    "C10 C11 C12 C13": (MURATA, "GRM21BR61C106KE15L", "ok", ""),
    "C14 C15 C16 C17": (MURATA, "GRM188R71H103KA01D", "TBD", "10 nF placeholder; CT value from the TPS22997 datasheet"),
    "R11 R12 R13 R14": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "R15 R16 R17 R18": (YAGEO, "RC0603FR-0747KL", "TBD", "or Pico internal pull-ups (decision open)"),
    "U7": (TI, "TPS61235PRWLT", "verify", "also sold as the larger reel TPS61235PRWLR"),
    "L2": ("Wurth Elektronik", "74438357010", "TBD", "same part as L1 if the TPS61235P datasheet accepts 1 uH / 6.2 A"),
    "C18 C19": (MURATA, "GRM21BR61C106KE15L", "ok", ""),
    "C20 C21 C22": (MURATA, "GRM31CR61A226KE19L", "verify", "22 uF 10 V X5R 1206; count from the datasheet"),
    "R19": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "R20": (YAGEO, "RC0603FR-07xxxxL", "TBD", "boost current-limit resistor (~2.5 A) from the datasheet"),
}

# frame parts already placed on the board (not in design.FRAME_BOM): refs, qty, value, (mfr, MPN, status, note)
FRAME_PLACED = [
    ("J1 J2 J3 J4", 1, "2.54 mm male header strip 1x40 (ESC seats: 28 pins, 4 + 3 per ESC)",
     ("Sullins", "PRPC040SAAN-RC", "ok", "1x40 break-away strip, cut to 4 + 3")),
    ("J5 J6", 2, "B2B socket 1x10 2.00 mm, frame bottom",
     ("Samtec", "SMM-110-02-S-S", "TBD", "SMT socket, needs 6 mm standoffs; current design = Bitcraze socket from Bitcraze (5 mm)")),
    ("J7", 1, "JST-SH 4, Pi USB", ("JST", "SM04B-SRSS-TB(LF)(SN)", "ok", "")),
    ("J8", 1, "JST-PH 2 vertical, Pi 5.1 V", ("JST", "B2B-PH-K-S(LF)(SN)", "ok", "")),
]

# FC module: refs, qty, value, (mfr, MPN, status, note)
FC_PARTS = [
    ("U1", 1, "Raspberry Pi Pico 2 W", ("Raspberry Pi", "SC1633", "verify", "Pico 2 W without headers")),
    ("U2", 1, "BMI088 IMU", ("Bosch Sensortec", "BMI088", "ok", "")),
    ("U3", 1, "BMP388 barometer", ("Bosch Sensortec", "BMP388", "ok", "")),
    ("C1 C2", 2, "100nF 16V", (MURATA, "GRM188R71H104KA93D", "ok", "100 nF 50 V X7R 0603")),
    ("P1 P2", 2, "2.00 mm male 1x10 SMD vertical (to the Flow deck)",
     ("Samtec", "TMM-110-01-L-S-SM", "verify", "0.5 mm square posts; check the post length vs the Flow deck sockets")),
    ("J1 J2", 2, "2.00 mm male 1x10 THT (to the frame)",
     ("Samtec", "TMM-110-01-L-S", "verify", "mates SMM; post length vs the chosen socket / standoff")),
    ("J9", 1, "JST-SH 3 horizontal, SWD", ("JST", "SM03B-SRSS-TB(LF)(SN)", "DNP", "fit when SWD is needed")),
    ("SW1", 1, "BOOTSEL tactile switch", ("Omron", "B3U-1000P", "ok", "top-actuated, 3.0 x 2.5 mm")),
]

# Mechanical stack (FC on the 4 cover holes) - generic hardware, any vendor
MECH_PARTS = [
    ("-", 4, "M2 x 5 mm hex standoff F-F, 4 mm AF (6 mm if the Samtec socket is chosen)",
     ("any", "M2x5 F-F standoff", "TBD", "length follows the J5/J6 decision")),
]


# ---------------------------------------------------------------------------
# Digi-Key part numbers and lifecycle, from the design doc's parts table (Nov 27 2026, looked up on
# digikey.com outside the build container). Cut-tape SKUs where one exists.
# MPN -> (Digi-Key PN or "", lifecycle / availability note)
# ---------------------------------------------------------------------------
DIGIKEY = {
    "USB4105-GF-A": ("2073-USB4105-GF-ACT-ND", ""),
    "BQ25606RGER": ("296-47743-1-ND", ""),
    "XAL4020-102MEC": ("2457-XAL4020-102MEC-ND", "replaced by Wurth 74438357010"),
    "74438357010": ("732-11197-1-ND", "in stock (user, Nov 2026)"),
    "RC0603FR-075K1L": ("311-5.10KHRCT-ND", ""),
    "RC0603FR-075K23L": ("311-5.23KHRCT-ND", "Digi-Key PN by the Yageo 311-<value>HRCT-ND pattern - confirm"),
    "RC0603FR-0730K9L": ("311-30.9KHRCT-ND", "Digi-Key PN by the Yageo 311-<value>HRCT-ND pattern - confirm"),
    "CL10B105KA8NNNC": ("1276-1184-1-ND", "Digi-Key PN not looked up here - confirm"),
    "RC0603FR-07226RL": ("311-226HRCT-ND", ""),
    "RC0603FR-07150RL": ("311-150HRCT-ND", ""),
    "103AT-2": ("4316-103AT-2-ND", "bulk"),
    "GRM21BR61C106KE15L": ("490-3886-1-ND", ""),
    "GRM188R61A475KE15D": ("490-10477-1-ND", "OBSOLETE - Digi-Key upgrade: GRM188R61A475KAAJD (490-14373-1-ND)"),
    "GRM188R71H473KA61D": ("", "not found at Digi-Key under this MPN - pick an active 47 nF 0603"),
    "LTST-C191KRKT": ("160-1447-1-ND", "0603 - replaced by the 0805 LTST-C171KRKT"),
    "LTST-C171KRKT": ("160-1427-1-ND", "Digi-Key PN from memory - confirm"),
    "RC0603FR-072K2L": ("311-2.20KHRCT-ND", ""),
    "TPS22810DBVR": ("296-45297-1-ND", ""),
    "PCM12SMTR": ("401-2016-1-ND", "LAST-TIME BUY - replaced by APEM MA12RTR"),
    "MA12RTR": ("563-1102-1-ND", "active (user, Nov 2026)"),
    "GRM188R71C105KA12D": ("", "not found at Digi-Key under this MPN - pick an active 1 uF 0603"),
    "RC0603FR-07156KL": ("311-156KHRCT-ND", ""),
    "RC0603FR-07100KL": ("311-100KHRCT-ND", ""),
    "RC0603FR-071M27L": ("311-1.27MHRCT-ND", ""),
    "TPS22997RYZR": ("296-TPS22997RYZRCT-ND", ""),
    "GRM188R71H103KA01D": ("", "end of life at distributors - pick an active 10 nF 0603"),
    "RC0603FR-0747KL": ("311-47.0KHRCT-ND", ""),
    "TPS61235PRWLT": ("296-44628-1-ND", ""),
    "GRM31CR61A226KE19L": ("", "not found at Digi-Key under this MPN - pick an active 22 uF 1206"),
    "PRPC040SAAN-RC": ("S1011EC-40-ND", "bulk"),
    "SMM-110-02-S-S": ("", "not listed (Digi-Key stocks the -LC clip version); Samtec direct / Mouser"),
    "SM04B-SRSS-TB(LF)(SN)": ("455-SM04B-SRSS-TBCT-ND", ""),
    "B2B-PH-K-S(LF)(SN)": ("455-1704-ND", "bulk"),
    "SC1633": ("2648-SC1633CT-ND", ""),
    "BMI088": ("828-1082-1-ND", ""),
    "BMP388": ("828-1079-1-ND", "OBSOLETE - BMP390 (828-BMP390CT-ND) is the same 10-LGA 2x2 package, active"),
    "GRM188R71H104KA93D": ("", "end of life at distributors - pick an active 100 nF 0603"),
    "TMM-110-01-L-S-SM": ("", "not listed in this variant; Samtec direct / Mouser, or a listed variant"),
    "TMM-110-01-L-S": ("", "not listed in this variant; Samtec direct / Mouser, or a listed variant"),
    "SM03B-SRSS-TB(LF)(SN)": ("455-SM03B-SRSS-TBCT-ND", ""),
    "B3U-1000P": ("SW1020CT-ND", ""),
}

# ---------------------------------------------------------------------------
# Datasheet verification log: MPN -> list of (document in Materials/, what it confirmed / still open).
# Files live in Materials/bom_datasheets/ (named <MPN>_<maker>_<kind>.pdf) unless a path says otherwise.
# Index: Materials/bom_datasheets/README.md (tools/datasheet_index.py).
# ---------------------------------------------------------------------------
DATASHEETS = {
    "MA12RTR": [
        ("MA12RTR_APEM_datasheet.pdf",
         "CONFIRMED (APEM MA series): 1P2T, right-angle actuator, 1.5 mm travel, body 6.7 x 2.6 x 1.4 mm; "
         "300 mA at 4 VDC, 70 mOhm, 10k cycles, -10..+60 C, reflow 260 C 1 min / iron 305 C 6 s. PCB layout = "
         "KiCad SW_SPDT_PCM12 pad positions (terminals -2.25/+0.75/+2.25 mm, bosses +-1.5 mm, shell tabs) and = "
         "BetzDrive apem-MA12RTR.kicad_mod. Common = middle terminal (pad 2 = SW_SPDT pin B). Use: EN/UVLO signal at "
         "<= 4.2 V, uA - within rating in current; the 4 VDC figure is a switching rating. Actuator side to the frame edge."),
    ],
    "TPS22810DBVR": [
        ("TPS22810DBVR_TI_datasheet.pdf",
         "CONFIRMED (SLVSDH0C rev C): DBV pinout 1 VIN, 2 GND, 3 EN/UVLO, 4 CT, 5 QOD, 6 VOUT = KD_Power:TPS22810DBV; "
         "DBV0006A land pattern (1.1 x 0.6 mm pads, 0.95 mm pitch, rows 2.6 mm) fits KiCad SOT-23-6 (same pitch/order, "
         "pads 1.325 mm reaching further in). 2.7-18 V, 2 A (DBV), RON 83 mOhm typ / 125 max at 3.3 V (0.06 V at 0.5 A). "
         "Internal VIN UVLO 2.54 V rising (2.00-2.62), 125 mV hysteresis -> off ~2.41 V. EN 1.23 V on (1.13-1.30), 1.13 V "
         "off, < 0.75 V shutdown (< 1 uA): SPDT EN/UVLO to VIN (on) / GND (off) is allowed (EN up to 18 V, must not float). "
         "Divider option R8 156 k / R9 100 k / R10 1.27 M (VOUT -> EN): on 3.30 V, off 2.70 V - confirmed, needs QOD "
         "active and the SPDT switching the divider top, not EN directly. QOD tied to VOUT: RPD 250-400 Ohm. CT may float "
         "(no part fitted)."),
    ],
    "103AT-2": [
        ("103AT-2_Semitec_AT_thermistor.pdf",
         "CONFIRMED: R25 10.0 k +-1 %, B25/85 3435 K +-1 % (the NTC TI recommends for the BQ25606 TS pin), "
         "thermal time constant ~15 s, 0.5 mm square leads at 2.54 mm, body 3.7 x 2.4 x 4.0 mm max. "
         "With R5 5.23 k / R6 30.9 k and the BQ25606 VT1/VT5 thresholds: charge window ~0-60 C "
         "(B model 1.5 / 60.0 C; TI's table 0 / 60 C; tolerances -1.5..4.3 C / 57.5..61.9 C); JEITA steps at "
         "~11 C and ~45 C. CHANGED: footprint from a 3.6 mm / 0.4 mm-drill wire pad to 2.54 mm, 1.0 mm drill "
         "(lead diagonal 0.71 mm)."),
    ],
    "74438357010": [
        ("74438357010_Wurth_datasheet.pdf",
         "CONFIRMED (WE-MAPI, rev 003.002): 1 uH +-20 %, Isat 6.2 A @ -10 % (12.5 A @ -30 %), IRP 10.25 A (40 K), "
         "RDC 11.6 typ / 13.5 max mOhm, 4.1 x 4.1 x 3.1 mm max, -40..+125 C, AEC-Q200. Charger needs Isat >= 3.42 A: OK. "
         "Land pattern 1 (0.98 x 3.7 mm pads, 3.35 mm span) = KiCad Inductor_SMD:L_Wuerth_MAPI-4030. "
         "Layout: no vias or traces under the inductor; 3.1 mm height to check at frame placement. "
         "L2 (boost): value still from the TPS61235P datasheet."),
    ],
    "BQ25606RGER": [
        ("BQ25606RGER_TI_datasheet.pdf",
         "CONFIRMED (SLUSCK6C rev C, Sep 2021): pinout = KD_Power:BQ25606 (all 25 pins); RGE0024H land pattern "
         "(24x 0.24x0.58 mm, EP 2.7 mm, vias 1.1 mm grid) = KiCad Texas_RGE0024H pad positions (KiCad pads longer "
         "outward: fine for hand soldering); R3 226 R -> ICHG = 677/226 = 3.0 A (2.83-3.16 A); R4 150 R -> "
         "ILIM = 478/150 = 3.19 A (3.06-3.33 A), used only for 'unknown' adapters (SDP 0.5 A, DCP 2.4 A); TS divider "
         "5.23 k / 30.9 k for 103AT-2, 0-60 C; L 1 uH (ripple 0.83 A at 5 V, D=0.5 -> Isat >= 3.42 A); BTST 47 nF, "
         "REGN 4.7 uF 10 V, BAT 10 uF, VSET float = 4.208 V, CE low = charge on. CHANGED: VBUS 1 uF + PMID 2x10 uF; "
         "OTG (pin 6) must not float -> GND; VAC (pin 1) shorted to VBUS. OPEN: SYS total <= 20 uF for the internal "
         "loop compensation, but the TPS22810 and boost input caps also sit on SYS (~41 uF) - decide."),
    ],
    "USB4105-GF-A": [
        ("USB4105_GCT_product_spec_revA3.pdf",
         "CONFIRMED: VBUS pins A4/A9/B4/B9 5.0 A total (charger needs 3.2 A max), GND A1/A12/B1/B12 6.25 A, "
         "48 V DC, -40..+85 C; reflow peak 255 C (+5/-0), 50 s above 230 C. KiCad symbol "
         "USB_C_Receptacle_USB2.0_16P pins = footprint pads (A1-B12 + S1). "
         "OPEN: no dimensions in this spec ('refer to drawing') - the land pattern needs the GCT drawing "
         "gct.co/files/drawings/usb4105.pdf (cited by the KiCad footprint)."),
    ],
    "SC1633": [("../RPi_Pico_2_W_datasheet.pdf", "CONFIRMED: pinout, Fig. 5 footprint; TP/SWD names from the module photo")],
    "BMI088": [("../crazyflie_bolt_1_1_revh_schematic.pdf", "CONFIRMED: pin numbers and wiring (reference design). OPEN: Bosch datasheet for the pad-1 corner")],
    "BMP388": [("../crazyflie_bolt_1_1_revh_schematic.pdf", "CONFIRMED: wiring (reference design). OPEN: Bosch datasheet; part obsolete -> BMP390")],
    "SMM-110-02-S-S": [("../samtec_SMM_2mm_socket_strip.pdf", "CONFIRMED: 3.68 mm SMT height, 2.00 mm pitch, 0.5 mm sq posts")],
}
