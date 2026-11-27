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
    "L1": ("Coilcraft", "XAL4020-102MEC", "ok", "1.0 uH, Isat well above 3.6 A"),
    "R1 R2": (YAGEO, "RC0603FR-075K1L", "ok", ""),
    "R3": (YAGEO, "RC0603FR-07226RL", "ok", ""),
    "R4": (YAGEO, "RC0603FR-07150RL", "ok", ""),
    "R5 R6": (YAGEO, "RC0603FR-07xxxxL", "TBD", "TS divider values from the BQ25606 datasheet + 103AT table"),
    "TH1": ("Semitec", "103AT-2", "verify", "Mouser stocks it; Digi-Key may list it as 103AT-2-ND"),
    "C1": (MURATA, "GRM21BR61C106KE15L", "ok", "10 uF 16 V X5R 0805"),
    "C2": (MURATA, "GRM21BR61C106KE15L", "ok", "10 uF 16 V X5R 0805"),
    "C3 C4": (MURATA, "GRM21BR61C106KE15L", "ok", "16 V part on the 10 V lines: less DC-bias loss"),
    "C5": (MURATA, "GRM21BR61C106KE15L", "ok", ""),
    "C6": (MURATA, "GRM188R61A475KE15D", "ok", "4.7 uF 10 V X5R 0603"),
    "C7": (MURATA, "GRM188R71H473KA61D", "ok", "47 nF 50 V X7R 0603"),
    "D1": ("Lite-On", "LTST-C191KRKT", "ok", "red 0603"),
    "R7": (YAGEO, "RC0603FR-072K2L", "ok", ""),
    "U2": (TI, "TPS22810DBVR", "ok", "SOT-23-6 (DBV)"),
    "SW1": ("C&K", "PCM12SMTR", "ok", "SPDT slide, SMD"),
    "C8 C9": (MURATA, "GRM188R71C105KA12D", "ok", "1 uF 16 V X7R 0603"),
    "R8 R9 R10": (YAGEO, "RC0603FR-07156KL / -07100KL / -071M27L", "DNP", "UVLO divider option"),
    "U3 U4 U5 U6": (TI, "TPS22997RYZR", "ok", ""),
    "C10 C11 C12 C13": (MURATA, "GRM21BR61C106KE15L", "ok", ""),
    "C14 C15 C16 C17": (MURATA, "GRM188R71H103KA01D", "TBD", "10 nF placeholder; CT value from the TPS22997 datasheet"),
    "R11 R12 R13 R14": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "R15 R16 R17 R18": (YAGEO, "RC0603FR-0747KL", "TBD", "or Pico internal pull-ups (decision open)"),
    "U7": (TI, "TPS61235PRWLT", "verify", "also sold as the larger reel TPS61235PRWLR"),
    "L2": ("Coilcraft", "XAL4020-102MEC", "TBD", "value from the TPS61235P datasheet"),
    "C18 C19": (MURATA, "GRM21BR61C106KE15L", "ok", ""),
    "C20 C21 C22": (MURATA, "GRM31CR61A226KE19L", "verify", "22 uF 10 V X5R 1206; count from the datasheet"),
    "R19": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "R20": (YAGEO, "RC0603FR-07xxxxL", "TBD", "boost current-limit resistor (~2.5 A) from the datasheet"),
}

# frame parts already placed on the board (not in design.FRAME_BOM): refs, qty, value, (mfr, MPN, status, note)
FRAME_PLACED = [
    ("J1 J2 J3 J4", 28, "2.54 mm male header pins (ESC seats, 4 + 3 per ESC)",
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
    ("C1 C2", 2, "100 nF 0603", (MURATA, "GRM188R71H104KA93D", "ok", "100 nF 50 V X7R 0603")),
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
