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
    "C14 C15 C16 C17": (MURATA, "GRM188R71H332KA01D", "ok", "3.3 nF 50 V X7R 0603 (stock book; >= 30 V needed)"),
    "R11 R12 R13 R14": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "R15 R16 R17 R18": (YAGEO, "RC0603FR-0747KL", "TBD", "or Pico internal pull-ups (decision open)"),
    "U7": (TI, "TPS61235PRWLT", "ok", "also sold as the larger reel TPS61235PRWLR"),
    "L2": ("Wurth Elektronik", "74438357010", "ok", "same part as L1; TPS61235P wants 0.7-1.3 uH effective"),
    "C18 C19": (MURATA, "GRM21BR61C106KE15L", "ok", ""),
    "C20 C21 C22": ("Samsung", "CL31B226KPHNFNE", "ok", "22 uF 10 V X7R 1206 (user pick, Digi-Key 1276-3145-1-ND)"),
    "R19": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "R20": (YAGEO, "RC0603FR-0749K9L", "ok", "CC 2.49 A (E24 fallback 51k = 2.44 A)"),
    "C24": (MURATA, "GRM188R71H103KA01D", "ok", "10 nF 0603, stock book"),
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
    ("U2", 1, "BMI088 IMU", ("Bosch Sensortec", "BMI088", "ok", "pin 2 (NC) to GND per Bosch")),
    ("U3", 1, "BMP390 barometer", ("Bosch Sensortec", "BMP390", "ok", "replaces the obsolete BMP388, same LGA-10 footprint")),
    ("C1 C2", 2, "100nF 16V", (MURATA, "GRM188R71H104KA93D", "ok", "100 nF 50 V X7R 0603")),
    ("P1 P2", 2, "2.00 mm male 1x10 SMD vertical (to the Flow deck)",
     ("Samtec", "TMM-110-04-L-S-SM", "verify", "-04: 1.91 mm post into the Flow deck's 2.1 mm Bitcraze sockets; check availability")),
    ("J1 J2", 2, "2.00 mm male 1x10 THT (to the frame)",
     ("Samtec", "TMM-110-01-L-S", "ok", "-01: 3.20 mm post, 1.8 mm into the Bitcraze socket on 5 mm standoffs (-02 for SMM on 6 mm)")),
    ("J9", 1, "JST-SH 3 horizontal, SWD", ("JST", "SM03B-SRSS-TB(LF)(SN)", "DNP", "fit when SWD is needed")),
    ("SW1", 1, "BOOTSEL tactile switch", ("Aratas (formerly Omron)", "B3U-1000P", "ok", "top-actuated, 3.0 x 2.5 x 1.6 mm")),
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
    "GRM188R71H103KA01D": ("", "end of life at distributors - replaced by 3.3 nF 50 V (stock)"),
    "RC0603FR-0747KL": ("311-47.0KHRCT-ND", ""),
    "TPS61235PRWLT": ("296-44628-1-ND", ""),
    "GRM31CR61A226KE19L": ("", "not found at Digi-Key - replaced by Samsung CL31B226KPHNFNE"),
    "CL31B226KPHNFNE": ("1276-3145-1-ND", "active (user, Nov 2026)"),
    "PRPC040SAAN-RC": ("S1011EC-40-ND", "bulk"),
    "SMM-110-02-S-S": ("", "not listed (Digi-Key stocks the -LC clip version); Samtec direct / Mouser"),
    "SM04B-SRSS-TB(LF)(SN)": ("455-SM04B-SRSS-TBCT-ND", ""),
    "B2B-PH-K-S(LF)(SN)": ("455-1704-ND", "bulk"),
    "SC1633": ("2648-SC1633CT-ND", ""),
    "BMI088": ("828-1082-1-ND", ""),
    "BMP388": ("828-1079-1-ND", "OBSOLETE - replaced by BMP390"),
    "BMP390": ("828-BMP390CT-ND", "active (user, Nov 2026)"),
    "GRM188R71H104KA93D": ("", "end of life at distributors - pick an active 100 nF 0603"),
    "TMM-110-04-L-S-SM": ("", "Samtec direct / Mouser; -04 is a non-standard length at Samtec - confirm"),
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
    "B3U-1000P": [
        ("B3U-1000P_Omron-Aratas_datasheet.pdf",
         "CONFIRMED: top-actuated, 3.0 x 2.5 mm body 1.2 mm high, plunger to 1.6 mm, 1.5 N, 1-50 mA / 3-12 VDC, "
         "-25..+70 C. PCB pads 0.8 x 1.7 mm at +-1.7 mm (2.6 inner / 4.2 outer) = KiCad SW_SPST_B3U-1000P centres "
         "(KiCad pads 0.9 mm wide). BOOTSEL current is below the 1 mA rating minimum - normal for a logic button."),
    ],
    "SM04B-SRSS-TB(LF)(SN)": [
        ("JST_SH_series_catalog.pdf",
         "CONFIRMED: SH 1.0 mm, 1.0 A, 50 V, -25..+85 C; side-entry PCB layout: signal pads 0.6 x 1.55 at 1.0 mm, MP pads "
         "1.2 x 1.8 with the inner edge 0.7 from the last pin centre, 3.875 mm signal-to-MP = KiCad "
         "JST_SH_SM04B-SRSS-TB (MP at +-2.8). Height 2.95 mm, depth 6.25 mm."),
    ],
    "SM03B-SRSS-TB(LF)(SN)": [
        ("JST_SH_series_catalog.pdf", "CONFIRMED: same layout rules as SM04B; = KiCad JST_SH_SM03B-SRSS-TB (MP at +-2.3)."),
    ],
    "B2B-PH-K-S(LF)(SN)": [
        ("JST_PH_series_catalog.pdf",
         "CONFIRMED: PH 2.0 mm, 2 A, 100 V, -40..+105 C; through-hole top entry: holes 0.7 +0.1/-0 mm at 2.0 mm = KiCad "
         "JST_PH_B2B-PH-K (0.75 mm drill) and the frame's DXF holes (0.75 mm); JST suggests the larger end (0.8) for FR4."),
    ],
    "GRM21BR61C106KE15L": [
        ("GRM21BR61C106KE15L_Murata_catalog_page.pdf",
         "CONFIRMED (Murata MLCC catalog 2021, p.109): 10 uF +-10 %, 16 Vdc, X5R, 2.0 x 1.25 mm (0805)."),
    ],
    "CL31B226KPHNFNE": [
        ("(no Samsung datasheet in the repo yet)",
         "OPEN: Digi-Key description 22 uF 10 V X7R 1206 (CL31 = 1206, B = X7R, 226 = 22 uF, K = 10 %, P = 10 V). "
         "Need the DC-bias curve: 3 x 22 uF must stay >= 20 uF effective at 5.1 V for the TPS61235P."),
    ],
    "TMM-110-01-L-S": [
        ("TMM-1xx-01_Samtec_TH_drawing.pdf",
         "CONFIRMED (F-226): 2.00 mm pitch, 0.5 mm posts, plastic 1.50 mm, 1.97 mm wide; lead style -01: post 3.20, tail "
         "3.50 (A 8.20); -02: 3.70 / 3.00. On 5 mm standoffs with the 2.1 mm Bitcraze socket: 1.4 mm free, post 1.8 mm in; "
         "tail 1.9 mm below the 1.6 mm FC. With SMM-110-02 on 6 mm: use -02 (2.88 mm in, 0.85 mm past the contact point)."),
    ],
    "TMM-110-04-L-S-SM": [
        ("TMM-1xx-xx-SM_Samtec_SM_drawing.pdf",
         "CONFIRMED (F-226): plastic 1.50 mm sitting 1.27 mm above the board (2.77 mm to its top), single-row foot span "
         "4.83 mm (alternating) - fits KiCad PinHeader_1x10_P2.00mm_Vertical_SMD_Pin1Left (2.35 mm pads at +-1.175); "
         "post -01 3.20 / -04 1.91 / -05 1.65 / -06 4.27 mm. -04 (1.91) ~ Bitcraze's 2 mm pin: seats in the Flow deck's "
         "2.1 mm socket, deck top 4.87 mm below the FC (-01 would bottom out)."),
    ],
    "TPS61235PRWLT": [
        ("TPS61235PRWLT_TI_datasheet_SLVSCK4A.pdf",
         "CONFIRMED (SLVSCK4A rev A): pinout 1 PGND, 2 SW, 3 VIN, 4 CC, 5 AGND, 6 FB, 7 EN, 8 INACT, 9 VOUT = KD_Power:TPS61235P; "
         "RWL0009A land pattern = KD_Power footprint after adding the SW-pad tab (0.975 x 0.3 at y -0.02). VIN 2.3 V to "
         "VOUT - 0.6 (4.5 V); 5.1 V fixed, FB to VOUT; L 0.7-1.3 uH effective -> Wurth 1 uH OK (peak ~5.3 A at 2.5 A out "
         "< Isat 6.2 A); CI >= 4.7 uF, CO >= 20 uF effective (3 x 22 uF 10 V 1206 ~30 uF at 5.1 V); valley limit 6.5-9.5 A; "
         "CC: IOUT = 1.244 V / RCC x 100000 -> R20 49.9 k = 2.49 A, C24 10 nF in parallel; EN pull-down <= 1 M (R19 100 k); "
         "INACT to AGND. Note: CC mode is meant for resistive / power-managed loads - 2.5 A acts as a fault limit."),
    ],
    "TPS22997RYZR": [
        ("TPS22997RYZR_TI_datasheet.pdf",
         "CONFIRMED (SLVSGT0, Dec 2022): pinout 1 VBIAS, 2-3 VIN, 4 PG, 5 GND, 6 QOD, 7-8 VOUT, 9 CT, 10 ON = KD_Power:TPS22997. "
         "VIN 0.1-5.5 V (abs 6 V), VBIAS 1.5-5.5 V -> VBIAS tied to BAT; 10 A continuous, RON 4 mOhm typ / 6 max "
         "(0.34 W at 7.5 A, RthJA 83.7 C/W -> ~+28 C); ON VIH 0.8 V / VIL 0.35 V (Pico 3.3 V GPIO direct), internal "
         "500 k smart pull-down (the 100 k R11-R14 stay so the switch is off with the Pico unpowered); PG open drain, "
         "needs VBIAS, pull-up to any rail <= 5.5 V; QOD tied to VOUT uses RQOD; thermal shutdown 170 C typ, 20 C hyst. "
         "CT: tR = (0.1302 VIN + 0.0063) CT + 27.8 VIN + 30.5 us -> 3.3 nF = ~2.0 ms at 4.2 V; CT capacitor >= 30 V."),
        ("TPS22997_RYZ0010A_TI_package_MPQF651A.pdf",
         "CONFIRMED: RYZ0010A land pattern = KD_Power:Texas_RYZ0010A footprint (corner pads 0.575 x 0.25 at x +-0.6625 / "
         "y +-0.75, VIN/VOUT 0.825 x 0.25 at x +-0.5375 / y +-0.25, pads 5/10 0.25 x 0.575 at y +-0.9125); 0.8 mm max height."),
    ],
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
         "No dimensions in this spec; the land pattern is confirmed by the SnapMagic footprint (next entry)"),
        ("(SnapMagic GCT_USB4105-GF-A.kicad_mod, user-supplied, not redistributable)",
         "CONFIRMED: all 12 signal pads, 4 shield slots (0.6 x 1.7 / 0.6 x 1.4) and 2 x 0.65 NPTH identical to KiCad "
         "USB_C_Receptacle_GCT_USB4105-xx-A_16P (origin offset 1.075 mm); merged pads A1_B12 / A4_B9 / B4_A9 / B1_A12 = "
         "KiCad's paired pins."),
    ],
    "SC1633": [("../RPi_Pico_2_W_datasheet.pdf", "CONFIRMED: pinout, Fig. 5 footprint; TP/SWD names from the module photo")],
    "BMI088": [
        ("BMI088_Bosch_datasheet_BST-BMI088-DS001.pdf",
         "CONFIRMED (rev 1.9, Jan 2024): table 14 pinout = KD_Sensors:BMI088 (grounds 4 GNDA, 6 GNDIO); pin 2 NC -> GND in "
         "both modes (tie to GND); PS = GND selects SPI; VDD 2.4-3.6 V, VDDIO 1.2-3.6 V; unused INT pins DNC. Landing "
         "pattern 8.2: pads 0.25 x 0.675 mm, centres +-1.2625 (sides) / +-2.0125 (ends) - footprint updated (the earlier "
         "0.35 x 0.59 pads left 0.15 mm gaps). Pin 1 corner = fig. 6 top view = footprint."),
        ("../crazyflie_bolt_1_1_revh_schematic.pdf", "reference circuit: SPI, INT1 -> INT_ACC, INT2+INT3 -> INT_GYR, 100 nF"),
    ],
    "BMP390": [
        ("BMP390_Bosch_datasheet_BST-BMP390-DS002.pdf",
         "CONFIRMED (rev 1.7): table 52 pinout identical to the BMP388 (1 VDDIO, 2 SCK, 3/8/9 VSS, 4 SDI, 5 SDO, 6 CSB, 7 INT, "
         "10 VDD); LGA-10 2.0 x 2.0 x 0.75 mm, bottom-view pads 0.275 x 0.25 (sides, 1.525 / 1.000 mm) and 0.25 x 0.275 "
         "(ends, 0.5 mm) = KD_Sensors:Bosch_LGA-10 footprint: drop-in for the obsolete BMP388."),
    ],
    "SMM-110-02-S-S": [("../samtec_SMM_2mm_socket_strip.pdf", "CONFIRMED: 3.68 mm SMT height, 2.00 mm pitch, 0.5 mm sq posts")],
}
