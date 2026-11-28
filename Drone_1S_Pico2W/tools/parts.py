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
    "R3": (YAGEO, "RC0603FR-07240RL", "ok", "E24 (sample book): ICHG 2.82 A"),
    "R4": (YAGEO, "RC0603FR-07150RL", "ok", ""),
    "R5": (YAGEO, "RC0603FR-075K1L", "ok", "E24 with R6 30k: TS window 2-61 C (datasheet 9.3.5 gives 5.23k / 30.9k)"),
    "R6": (YAGEO, "RC0603FR-0730KL", "ok", "E24 with R5 5.1k"),
    "TH1": ("Semitec", "103AT-2", "ok", "10 k +-1 %, B 3435 K +-1 %, radial 2.54 mm"),
    "C1": ("Samsung", "CL10B105KA8NNNC", "verify", "1 uF 25 V X7R 0603"),
    "C2 C23": (MURATA, "GRM21BR61E106KA73L", "ok", "10 uF 25 V X5R 0805 (user 2026-11-28, in stock at Digi-Key)"),
    "C3 C4": (MURATA, "GRM21BR61E106KA73L", "ok", "25 V part on the 4.4 V line: less DC-bias loss"),
    "C5": (MURATA, "GRM21BR61E106KA73L", "ok", ""),
    "C6": (MURATA, "GRM188R61A475KE15D", "ok", "4.7 uF 10 V X5R 0603"),
    "C7": (MURATA, "GRM188R71H473KA61D", "ok", "47 nF 50 V X7R 0603"),
    "D1": ("Lite-On", "LTST-C171KRKT", "verify", "red 0805 (LEDs are 0805 in this repo)"),
    "R7": (YAGEO, "RC0603FR-072K2L", "ok", ""),
    "U2": (TI, "TPS22810DBVT", "ok", "SOT-23-6 (DBV); DBVT = small reel of the same part (user 2026-11-28, in stock)"),
    "SW1": ("Nidec Components", "CUS-12TB", "ok", "user 2026-11-28 (APEM MA12R/TR obsolete); PCM12 land pattern"),
    "C8 C9": (MURATA, "GRM188R71C105KA12D", "ok", "1 uF 16 V X7R 0603"),
    "R8 R9 R10": (YAGEO, "RC0603FR-07150KL / -07100KL / -071M27L", "DNP", "UVLO divider option 3.22 / 2.65 V (internal lockout used)"),
    "D2": ("onsemi", "MBR120VLSFT1G", "ok", "VSYS back-feed Schottky, SOD-123FL (as PicoBalancer D2)"),
    "U3 U4 U5 U6": (TI, "TPS22998RYZR", "ok", "TPS22997RYZR out of stock (user 2026-11-28); same RYZ footprint, pins 4/6 differ, no PG"),
    "C10 C11 C12 C13": (MURATA, "GRM21BR61E106KA73L", "ok", ""),
    "R15 R16 R17 R18": (YAGEO, "RC0603JR-070RL", "ok", "0R 0603, CT strap (stock book)"),
    "R11 R12 R13 R14": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "U7": (TI, "TPS61235PRWLR", "ok", "R reel variant ordered (same part as RWLT; as PicoBalancer)"),
    "L2": ("Wurth Elektronik", "74438357010", "ok", "same part as L1; TPS61235P wants 0.7-1.3 uH effective"),
    "C18 C19": (MURATA, "GRM21BR61E106KA73L", "ok", ""),
    "C20 C21 C22": ("Samsung", "CL31B226KPHNFNE", "ok", "22 uF 10 V X7R 1206 (user pick, Digi-Key 1276-3145-1-ND)"),
    "R19": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "R20": (YAGEO, "RC0603FR-0751KL", "ok", "E24 (sample book): CC 2.44 A"),
    "C24": (MURATA, "GRM188R71H103KA01D", "ok", "10 nF 0603, stock book"),
}

# frame parts already placed on the board (not in design.FRAME_BOM): refs, qty, value, (mfr, MPN, status, note)
FRAME_PLACED = [
    ("J1 J2 J3 J4", 1, "2.54 mm male header strip 1x40 (ESC seats: 28 pins, 4 + 3 per ESC)",
     ("Sullins", "PRPC040SAAN-RC", "ok", "1x40 break-away strip, cut to 4 + 3")),
    ("J5 J6", 2, "B2B socket 1x10 2.00 mm SMD, frame bottom (mates with FC J1/J2)",
     ("Sullins", "NPPN101BFLD-RC", "ok", "4.6 mm tall, 7 mm printed spacers; nylon: hand-solder after reflow; footprint update pending")),
    ("J7", 1, "JST-SH 4 vertical (top entry), Pi USB", ("JST", "BM04B-SRSS-TBT(LF)(SN)", "ok", "frame top, under the Pi's USB port; TBT = TB + pick-and-place cap (peel off), BM04B-SRSS-TB not available")),
    ("J8", 1, "JST-PH 2 vertical, Pi 5.1 V", ("JST", "B2B-PH-K-S(LF)(SN)", "ok", "")),
]

# FC module: refs, qty, value, (mfr, MPN, status, note)
FC_PARTS = [
    ("U1", 1, "Raspberry Pi Pico 2 W", ("Raspberry Pi", "SC1633", "ok", "Pico 2 W without headers; ordered from Mouser (user 2026-11-28), not Digi-Key")),
    ("U2", 1, "BMI088 IMU", ("Bosch Sensortec", "BMI088", "ok", "pin 2 (NC) to GND per Bosch")),
    ("U3", 1, "BMP390 barometer", ("Bosch Sensortec", "BMP390", "ok", "replaces the obsolete BMP388, same LGA-10 footprint")),
    ("C1 C2", 2, "100nF 16V", (MURATA, "GRM188R71H104KA93D", "ok", "100 nF 50 V X7R 0603")),
    ("P1 P2", 2, "2.00 mm male 1x10 SMD vertical (to the Flow deck)",
     ("Samtec", "TMM-110-01-T-S-SM-P-TR", "ok", "same SM footprint as -04; 3.20 mm tin post: TRIM to ~1.9 mm after soldering, else the deck hangs ~1.3 mm lower; pull off the -P pick-and-place cap")),
    ("J1 J2", 2, "2.00 mm male 1x10 THT (to the frame)",
     ("Wurth Elektronik", "62001011121", "ok", "plastic 2.0, pin 4.0: ~3.6 mm into the Sullins socket on the 7 mm spacers")),
    ("J9", 1, "JST-SH 3 horizontal, SWD", ("JST", "SM03B-SRSS-TB(LF)(SN)", "DNP", "fit when SWD is needed")),
    ("SW1", 1, "BOOTSEL tactile switch", ("Aratas (formerly Omron)", "B3U-1000PM-B", "ok", "with boss: footprint SW_SPST_B3U-1000P-B (0.8 mm hole)")),
    # added at routing (stage 2/3, 2026-11-28): sensor supply filter, pull-ups, DShot series resistors
    ("L1", 1, "1uH 0603 (sensor supply filter, 3V3 -> 3V3_SENS)", ("TDK", "MLZ1608N1R0LT000", "ok", "as the Crazyflie Bolt 1.1 (MLZ1608); 700 mA rated (Digi-Key lists Isat 140 mA) for a few mA load")),
    ("C3", 1, "4.7uF 10V 0603 (3V3_SENS bulk)", (MURATA, "GRM188R61A475KAAJD", "ok", "stock book")),
    ("R1 R2", 2, "4.7k 0603 (I2C pull-ups)", (YAGEO, "RC0603FR-074K7L", "ok", "stock book")),
    ("R3 R4 R5 R6", 4, "100R 0603 (DShot series)", (YAGEO, "RC0603FR-07100RL", "ok", "stock book")),
    ("R7", 1, "47k 0603 (MOTOR_PG pull-up)", (YAGEO, "RC0603FR-0747KL", "ok", "stock book")),
]

# Qwiic deck (deck_design.py): Flow-deck-format adapter with a SparkFun Qwiic connector (user 2026-11-28).
# refs, qty, value, (mfr, MPN, status, note)
DECK_PARTS = [
    ("J1 J2", 2, "2.00 mm 1x10 SMD socket onto the FC's P1 / P2",
     ("Sullins", "NPPN101BFLD-RC", "ok", "same socket as the frame J5/J6; the FC's P1/P2 posts stay at 3.20 mm (untrimmed) on an FC used with this deck")),
    ("J3", 1, "Qwiic: JST SH 4-pin right-angle (GND, 3V3, SDA, SCL)", ("JST", "SM04B-SRSS-TB(LF)(SN)", "ok", "bottom, rear edge")),
    ("C1", 1, "1uF 16V 0603", (MURATA, "GRM188R71C105KA12D", "ok", "Qwiic 3V3 decoupling (stock book)")),
]

# Mechanical stack and printed-part hardware (from the OpenSCAD model 1S_PiZero.scad, screw lengths computed there).
# Generic parts: Digi-Key numbers to be filled in (user). refs, qty, value, (mfr, MPN, status, note)
MECH_PARTS = [
    # FC stack (28 Nov 2026): one M2 x 20 through-bolt per shared hole - cover boss 4.0 + frame 2.0 + printed spacer 7.0
    # + FC 1.6 = 14.6 mm grip, nylon-insert nut under the FC. The spacer sets the board-to-board gap: the Wurth male +
    # Sullins socket seat at 6.6 mm (up to ~6.85 mm at tolerance), so the gap must stay >= 6.9 mm.
    ("FC stack", 4, "3D-printed spacer 7.0 mm (print 7.0-7.2, never < 6.9), OD 5 mm, hole 2.3 mm, PETG or ASA",
     ("any", "3D-printed spacer", "ok", "between frame and FC on the 4 cover holes; not PLA (creeps under the bolt, softens ~55 C); measure the length")),
    ("FC stack", 4, "M2 x 20 mm screw, galvanized steel (cover + frame + spacer + FC)", ("any", "M2x20 galvanized screw", "ok", "local: 4project.co.il/product/screw-m2x20mm-galvanized; head on the cover boss, down through everything")),
    ("FC stack", 4, "M2 nylon-insert lock nut (DIN 985)", ("any", "M2 nyloc nut DIN 985", "TBD", "under the FC; removing it frees the FC (and loosens the cover)")),
    ("Gear", 4, "M2.5 x 5 mm socket head screw (Ø5 washer max: the head sits 0.8 mm off the cover rail)", ("any", "M2.5x5 SHCS", "TBD", "landing-gear skids, from the frame top (M2.5 since 2026-11-28, scad len_gear)")),
    ("Gear", 4, "M2.5 brass heat-set insert, 4.0 mm OD x 4.0 mm", ("any", "M2.5 heat-set insert 4.0x4.0", "TBD", "landing-gear skid bosses (same insert as the Pi posts)")),
    ("Camera", 2, "M2 brass heat-set insert, 3.6 mm OD x 3.0 mm", ("any", "M2 heat-set insert 3.6x3.0", "TBD", "camera blocks")),
    ("Pi", 4, "M2.5 x 5 mm socket head screw", ("any", "M2.5x5 SHCS", "TBD", "Pi Zero 2 W into the cover posts")),
    ("Pi", 4, "M2.5 brass heat-set insert, 4.0 mm OD x 4.0 mm", ("any", "M2.5 heat-set insert 4.0x4.0", "TBD", "cover posts")),
    ("Camera", 2, "M2 x 6 mm socket head screw", ("any", "M2x6 SHCS", "TBD", "camera harness to the cover")),
    ("Motors", 16, "M2 x 5 mm screw (check against the motors' own)", ("any", "M2x5 motor screw", "TBD", "motors, from under the frame")),
]

# Cables and their mating housings / contacts (frame and FC connectors). Crimp parts or pre-crimped leads.
CABLE_PARTS = [
    # 2026-11-28 (user): pre-wired leads from the local supplier instead of housings + crimp contacts (SH crimping needs
    # JST's tool; SHR-04V-S-B was not at Digi-Key). Frame end plugs into J7 / J8, the free end is soldered at the Pi.
    ("J7 cable", 1, "JST SH-style 4-pin female, single-ended, 12 cm leads (to frame J7, Pi USB)",
     ("4project (Pololu 5520)", "4P-7209 / POL-5520", "ok",
      "local: 4project.co.il/product/jst-sh-style-cable-4pin-single-ended-female-12cm; Pi end soldered to the Pi Zero 2 W "
      "USB test pads (GND, D-, D+, GND); 'SH-style' clone - check the fit in J7 on the first build")),
    ("J8 cable", 1, "JST PH 2-pin female with wires (to frame J8, Pi 5.1 V)",
     ("4project", "4P-682", "ok",
      "local: 4project.co.il/product/jst-ph-2pin-connector-with-wires; Pi end to GPIO pin 4 (5 V) / 6 (GND); "
      "check the wire gauge (>= 26 AWG for the Pi Zero 2 W's ~1 A, peaks higher) and match the red lead to J8's + pin (set in the frame netlist)")),
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
    "GRM21BR61C106KE15L": ("490-3886-1-ND", "replaced by GRM21BR61E106KA73L (25 V)"),
    "GRM21BR61E106KA73L": ("490-5523-1-ND", "user, Nov 2026 (digikey.co.il)"),
    "GRM188R61A475KE15D": ("490-10477-1-ND", "OBSOLETE - Digi-Key upgrade: GRM188R61A475KAAJD (490-14373-1-ND)"),
    "GRM188R71H473KA61D": ("", "not found at Digi-Key under this MPN - pick an active 47 nF 0603"),
    "LTST-C191KRKT": ("160-1447-1-ND", "0603 - replaced by the 0805 LTST-C171KRKT"),
    "LTST-C171KRKT": ("160-1427-1-ND", "Digi-Key PN from memory - confirm"),
    "RC0603FR-072K2L": ("311-2.20KHRCT-ND", ""),
    "TPS22810DBVR": ("296-45297-1-ND", "large reel - the frame orders TPS22810DBVT"),
    "TPS22810DBVT": ("296-45304-1-ND", "user, Nov 2026 (digikey.co.il)"),
    "PCM12SMTR": ("401-2016-1-ND", "LAST-TIME BUY - replaced by Nidec CUS-12TB"),
    "MA12RTR": ("", "OBSOLETE - replaced by Nidec CUS-12TB"),
    "CUS-12TB": ("563-1102-1-ND", "active, 12 weeks lead time (user, Nov 2026)"),
    "GRM188R71C105KA12D": ("", "not found at Digi-Key under this MPN - pick an active 1 uF 0603"),
    "RC0603FR-07156KL": ("311-156KHRCT-ND", ""),
    "RC0603FR-07100KL": ("311-100KHRCT-ND", ""),
    "RC0603FR-071M27L": ("311-1.27MHRCT-ND", ""),
    "GRM188R71H103KA01D": ("", "end of life at distributors - replaced by 3.3 nF 50 V (stock)"),
    "RC0603FR-0747KL": ("311-47.0KHRCT-ND", ""),
    "TPS61235PRWLT": ("296-44628-1-ND", "the frame orders TPS61235PRWLR"),
    "TPS61235PRWLR": ("296-47376-1-ND", "R reel variant (user cart, Nov 2026)"),
    "GRM31CR61A226KE19L": ("", "not found at Digi-Key - replaced by Samsung CL31B226KPHNFNE"),
    "CL31B226KPHNFNE": ("1276-3145-1-ND", "active (user, Nov 2026)"),
    "PRPC040SAAN-RC": ("S1011EC-40-ND", "bulk"),
    "SMM-110-02-S-S": ("612-SMM-110-02-S-S-ND", "not used: replaced by Sullins NPPN101BFLD-RC"),
    "MBR120VLSFT1G": ("MBR120VLSFT1GOSCT-ND", "Digi-Key PN as PicoBalancer"),
    "NPPN101BFLD-RC": ("S5902-10-ND", "user, Nov 2026"),
    "62001011121": ("732-62001011121-ND", "user, Nov 2026"),
    "A03SR03SR30K51B": ("455-3708-ND", "not used: the Raspberry Pi Debug Probe's own SH-3 cable is used for J9"),
    "B3U-1000PM-B": ("39-B3U-1000PM-BCT-ND", "in stock at digikey.co.il (user, Nov 2026)"),
    "SM04B-SRSS-TB(LF)(SN)": ("455-SM04B-SRSS-TBCT-ND", ""),
    "BM04B-SRSS-TB(LF)(SN)": ("455-BM04B-SRSS-TBCT-ND", "not available (user, Nov 2026) - BM04B-SRSS-TBT ordered"),
    "BM04B-SRSS-TBT(LF)(SN)": ("455-BM04B-SRSS-TBTCT-ND", ""),
    "MLZ1608N1R0LT000": ("445-6753-1-ND", "cut tape"),
    "TPS22998RYZR": ("296-TPS22998RYZRCT-ND", "user cart, Nov 2026"),
    "TPS22997RYZR": ("296-TPS22997RYZRCT-ND", "OUT OF STOCK (user, Nov 2026) - replaced by TPS22998RYZR"),
    "B2B-PH-K-S(LF)(SN)": ("455-1704-ND", "bulk"),
    "SHR-04V-S-B": ("455-1379-ND", "out of stock at Digi-Key (25 wk, Nov 2026): SHR-04V-S (455-1394-ND) mates the same header"),
    "SSH-003T-P0.2-H": ("455-2963-1-ND", "cut tape"),
    "PHR-2": ("455-1165-ND", ""),
    "SPH-002T-P0.5S": ("455-1127-1-ND", "cut tape"),
    "SC1633": ("2648-SC1633CT-ND", ""),
    "BMI088": ("828-1082-1-ND", ""),
    "BMP388": ("828-1079-1-ND", "OBSOLETE - replaced by BMP390"),
    "BMP390": ("828-BMP390CT-ND", "active (user, Nov 2026)"),
    "GRM188R71H104KA93D": ("", "end of life at distributors - pick an active 100 nF 0603"),
    "TMM-110-04-L-S-SM": ("", "not used: non-standard length, hard to get - replaced by TMM-110-01-G-S-SM (trimmed)"),
    "TMM-110-01-G-S-SM": ("612-TMM-110-01-G-S-SM-ND", "not used: gold version out of stock"),
    "TMM-110-01-T-S-SM-P-TR": ("612-TMM-110-01-T-S-SM-P-CT-ND", "cut tape (user, Nov 2026)"),
    "TMM-110-01-L-S": ("SAM15328-ND", "not used: post too short for the Sullins socket"),
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
    "TPS22998RYZR": [
        ("TPS22998RYZR_TI_datasheet.pdf",
         "CONFIRMED (SLVSG05A): RYZ pinout 1 VBIAS, 2-4 VIN, 5 GND, 6-8 VOUT, 9 CT, 10 ON (no PG, no QOD pin; QOD fixed "
         "50 Ohm). VIN 0.2-5.5 V, VBIAS 2.2-5.5 V, 10 A; RON 4 mOhm typ, 6 max (VBIAS 5 V) / 7 max (VBIAS 3.3 V); ON "
         "VIH 0.765-1.035 V, VIL 0.595-0.805 V; CT tri-state: tRISE at VIN 3.3 V = 0.15 ms open / 1.23 ms VBIAS / 2.48 ms "
         "GND; TSD 130-180 C (150 typ), 20 C hysteresis. Package = TPS22997 RYZ0010A (same land pattern)."),
    ],
    "BM04B-SRSS-TBT(LF)(SN)": [
        ("JST_SH_series_catalog.pdf", "BM04B-SRSS-TB with a pick-and-place suction cap (JST TBT suffix); same footprint."),
    ],
    "BM04B-SRSS-TB(LF)(SN)": [
        ("JST_SH_series_catalog.pdf",
         "SH 1.0 mm top-entry (BM type), same family / housing SHR-04V-S-B as SM04B. Footprint = KiCad stock "
         "JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical: TO CONFIRM against the catalog's BM PCB layout drawing."),
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
    "GRM21BR61E106KA73L": [
        ("(no Murata page for this MPN in the repo yet)",
         "10 uF +-10 %, 25 Vdc, X5R, 0805 (Digi-Key listing 490-5523-1-ND). Thickness and DC-bias curve to confirm "
         "from the Murata page; same 0805 land pattern."),
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
    "TMM-110-01-T-S-SM-P-TR": [
        ("TMM-1xx-xx-SM_Samtec_SM_drawing.pdf",
         "CONFIRMED (F-226): -T matte tin, -P pick-and-place pad, -TR tape; same SM body and foot pattern as -04 = KiCad "
         "PinHeader_1x10_P2.00mm_Vertical_SMD_Pin1Left; -01 post 3.20 mm: trim to ~1.9 mm for the Flow deck's 2.1 mm "
         "socket. Tin post into the deck's gold contacts: fine for the few mating cycles here."),
    ],
    "TMM-110-01-G-S-SM": [
        ("TMM-1xx-xx-SM_Samtec_SM_drawing.pdf",
         "CONFIRMED (F-226): same SM body and foot pattern as -04 (plastic 1.50 at 1.27 above the board, 4.83 mm foot span) "
         "= KiCad PinHeader_1x10_P2.00mm_Vertical_SMD_Pin1Left; -01 post 3.20 mm. The Flow deck socket is 2.1 mm: trim the "
         "posts to ~1.9 mm (as -04) so the deck seats against the plastic; untrimmed the deck sits ~1.3 mm lower."),
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
    "CUS-12TB": [
        ("CUS-12TB_Nidec_CUS_series_catalog.pdf",
         "CONFIRMED (Nidec CUS catalog 2024-03): SPDT, non-shorting, right-angle (side) actuator, 1.5 mm travel, body "
         "6.7 x 2.6 x 1.4 mm, gull-wing; recommended pads = KiCad SW_SPDT_PCM12 (terminals 0.7 x 1.5 at -2.25 / +0.75 / "
         "+2.25 mm, phi 0.9 boss holes +-1.5 mm, shell tabs 1.0 x 0.8 at +-3.65 mm). Common = terminal 2 (SW_SPDT pin B). "
         "300 mA / 4 VDC, 10k cycles, -20..+70 C (Digi-Key). Use: EN/UVLO signal, uA."),
    ],
    "MA12RTR": [
        ("../connector_options/MA12RTR_APEM_datasheet_obsolete.pdf",
         "CONFIRMED (APEM MA series): 1P2T, right-angle actuator, 1.5 mm travel, body 6.7 x 2.6 x 1.4 mm; "
         "300 mA at 4 VDC, 70 mOhm, 10k cycles, -10..+60 C, reflow 260 C 1 min / iron 305 C 6 s. PCB layout = "
         "KiCad SW_SPDT_PCM12 pad positions (terminals -2.25/+0.75/+2.25 mm, bosses +-1.5 mm, shell tabs) and = "
         "BetzDrive apem-MA12RTR.kicad_mod. Common = middle terminal (pad 2 = SW_SPDT pin B). Use: EN/UVLO signal at "
         "<= 4.2 V, uA - within rating in current; the 4 VDC figure is a switching rating. Actuator side to the frame edge."),
    ],
    "TPS22810DBVT": [
        ("TPS22810DBVR_TI_datasheet.pdf",
         "Same device and DBV package as TPS22810DBVR (T = 250-piece reel, R = 3000): everything confirmed for DBVR applies."),
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
    "MBR120VLSFT1G": [("MBR120VLSFT1G_onsemi_datasheet.pdf",
                       "CONFIRMED (onsemi): 20 V, 1 A Schottky, very low VF, SOD-123FL = KiCad D_SOD-123F; battery OR-ing")],
    "62001011121": [
        ("62001011121_Wurth_datasheet.pdf",
         "CONFIRMED (rev 003.001, 2024-04-04): 2.00 mm, 0.5 mm sq gold, plastic 2.0, pin 4.0 above it, tail 2.7, hole 0.9 "
         "(KiCad PinHeader_1x10_P2.00mm 0.8 drill also fits the 0.71 mm diagonal), 2 A, 50 cycles."),
    ],
    "NPPN101BFLD-RC": [
        ("NPPN101BFLD-RC_Sullins_drawing_10489.pdf",
         "CONFIRMED (dwg 10489 rev H): SMD 2.00 mm female, body 4.40 (4.60 +-0.25 overall), contact point 2.50 below the "
         "top, 2.40 wide, pads 0.90 x 2.0 staggered at 5.20 outer span (D = pin-1 row per the D layout), 2 A, mates 0.5 sq "
         "posts. N = nylon 6T, wave / manual soldering only. With 62001011121 on 7 mm: ~3.6 mm in, 0.4 mm air."),
    ],
    "B3U-1000PM-B": [
        ("B3U-1000P_Omron-Aratas_datasheet.pdf",
         "CONFIRMED: same switch and pads as B3U-1000P, with locating boss (PM = 1,000 pack). Needs KiCad "
         "SW_SPST_B3U-1000P-B (0.8 mm NPTH at the centre)."),
    ],
    "SMM-110-02-S-S": [("../samtec_SMM_2mm_socket_strip.pdf", "CONFIRMED: 3.68 mm SMT height, 2.00 mm pitch, 0.5 mm sq posts")],
}
