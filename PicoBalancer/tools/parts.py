"""Orderable parts for PicoBalancer: MPN per design.BOM line, distributor numbers, datasheet log.

status: "ok"      value fixed, datasheet checked (or a part already verified on Drone_1S_Pico2W)
        "verify"  MPN / variant / distributor stock still to confirm on Digi-Key or Mouser
        "TBD"     waits for a decision (see the design doc "Open decisions")
        "DNP"     footprint only
Supply chain: Digi-Key or Mouser, whichever has stock. Lifecycle (active / NRND / obsolete) is verified by the user at the end of component selection (Digi-Key BOM
Manager); TI's product pages list BQ25606, TPS22810, TPS61235P as ACTIVE (checked 2026-11-27). Stock items (0603 R / C from the sample book,
0805 LEDs) are left out of the distributor CSV and listed in fabrication/BOM_stock.md.
"""

YAGEO, MURATA, TI = "Yageo", "Murata", "Texas Instruments"

# key = refs string of a design.BOM line -> (manufacturer, MPN, status, note)
MPN = {
    "U1": ("Raspberry Pi", "SC0919", "ok", "Pico WH (headers fitted) for the sockets; SC0918 = Pico W without headers; Pico 2 WH later"),
    "J1 J2": ("Sullins", "PPPC201LFBN-RC", "ok", "1x20 female 2.54 mm, 8.50 mm insulator"),
    "U2": ("CEVA", "BNO086", "ok", "LGA-28"),
    "Y1": ("Epson", "FC-135 32.7680KA-A5", "ok", "32.768 kHz, 12.5 pF, +-20 ppm (ordered, Digi-Key SER4103CT-ND)"),
    "C1 C2": (MURATA, "GRM1885C1H220JA01D", "ok", "22 pF C0G 0603 (stock)"),
    "C3 C4 C5": ("Samsung", "CL10B104KB8NNNC", "ok", "100 nF 50 V X7R 0603 (stock); replaces GRM188R71H104KA93D (EOL at distributors)"),
    "R1 R2": (YAGEO, "RC0603FR-0710KL", "ok", ""),
    "R3 R4": (YAGEO, "RC0603FR-0710KL", "ok", ""),
    "R5 R6": (YAGEO, "RC0603FR-074K7L", "ok", ""),
    "R7": (YAGEO, "RC0603FR-0710KL", "ok", ""),
    "U3 U4": ("Monolithic Power Systems", "MP6550GG-Z", "ok", "QFN-12 2 x 2 mm"),
    "C6 C7": (MURATA, "GRM21BR61E106KA73L", "ok", "10 uF 25 V X5R 0805 (ordered; replaces GRM21BR61C106KE15L)"),
    "C8 C9": ("Samsung", "CL10B105KA8NNNC", "ok", "1 uF 0603 (stock)"),
    "C10 C11": ("Samsung", "CL10B474KA8NNNC", "ok", "0.47 uF 0603 (stock)"),
    "R8 R9": (YAGEO, "RC0603FR-074K3L", "ok", "ISET 1.16 A for the Pololu 3072 (30:1 HPCB 6V)"),
    "C12 C13": (MURATA, "GRM1885C1H101JA01D", "ok", "100 pF C0G 0603 (stock)"),
    "R10": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "J3 J4": ("JST", "BM06B-SRSS-G-TB(LF)(SN)", "ok", "vertical (top entry); from Mouser 306-6BSRSSGTBLPP (the one non-Digi-Key line)"),
    "J7 J8": ("-", "pads only", "ok", "2 mm solder pads for direct wiring"),
    "U5": (TI, "TPS61235PRWLR", "ok", "ordered as the R reel variant (same part as RWLT)"),
    "L2": ("Wurth Elektronik", "74438357010", "ok", ""),
    "C14 C15": (MURATA, "GRM21BR61E106KA73L", "ok", ""),
    "C16 C17 C18": ("Samsung", "CL31B226KPHNFNE", "ok", "22 uF 10 V X7R 1206"),
    "R11": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "R12": (YAGEO, "RC0603FR-0749K9L", "ok", "E24 fallback 51k = 2.44 A"),
    "C19": ("Samsung", "CL10B103KB8NNNC", "ok", "10 nF 50 V X7R 0603 (stock); replaces GRM188R71H103KA01D (EOL)"),
    "J5": ("GCT", "USB4235-03-C", "ok", "vertical SMT, 6.5 mm; land pattern from GCT drawing sheet 2; fallback USB4120-03-C"),
    "U6": (TI, "BQ25606RGER", "ok", ""),
    "L1": ("Wurth Elektronik", "74438357010", "ok", ""),
    "R13 R14": (YAGEO, "RC0603FR-075K1L", "ok", ""),
    "R15": (YAGEO, "RC0603FR-07226RL", "ok", "E24 fallback 240 R = 2.82 A"),
    "R16": (YAGEO, "RC0603FR-07150RL", "ok", ""),
    "R17": (YAGEO, "RC0603FR-075K23L", "ok", "E24 fallback 5.1k"),
    "R18": (YAGEO, "RC0603FR-0730K9L", "ok", "E24 fallback 30k"),
    "TH1": ("Semitec", "103AT-2", "DNP", "charger temperature left out (user 2026-11-27); R19 fitted instead"),
    "R19": (YAGEO, "RC0603FR-0710KL", "ok", "fixed TS: 30.9k parallel 10k, with 5.23k -> TS = 0.59 REGN (normal window, ~25 C)"),
    "C20": ("Samsung", "CL10B105KA8NNNC", "ok", "1 uF 25 V 0603 (stock)"),
    "C21 C22": (MURATA, "GRM21BR61E106KA73L", "ok", ""),
    "C23 C24": (MURATA, "GRM21BR61E106KA73L", "ok", ""),
    "C25": (MURATA, "GRM21BR61E106KA73L", "ok", ""),
    "C26": (MURATA, "GRM188R61A475KAAJD", "ok", "4.7 uF 10 V X5R 0603 (stock); Digi-Key upgrade of the obsolete GRM188R61A475KE15D"),
    "C27": ("Samsung", "CL10B473KB8NNNC", "ok", "47 nF 50 V X7R 0603 (stock); replaces GRM188R71H473KA61D (not found at Digi-Key)"),
    "D1": ("Lite-On", "LTST-C171KRKT", "ok", "red 0805 (stock)"),
    "R20": (YAGEO, "RC0603FR-072K2L", "ok", ""),
    "U7": (TI, "TPS22810DBVT", "ok", "ordered as DBVT (small reel), same part as DBVR"),
    "SW1": ("NKK Switches", "AS12AP", "ok", "non-shorting; alternative SS12SDP4 (shorting, needs R34) also ordered"),
    "R34": (YAGEO, "RC0603FR-071KL", "ok", ""),
    "C28 C29": ("Samsung", "CL10B105KA8NNNC", "ok", "1 uF 0603 (stock)"),
    "R21": (YAGEO, "RC0603FR-070RL", "ok", "0R default (internal UVLO); RC0603FR-07156KL for the 2.70 V option"),
    "R22 R23": (YAGEO, "RC0603FR-07100KL / -071M27L", "DNP", "fit with R21 = 156k for 3.30 / 2.70 V"),
    "D2": ("onsemi", "MBR120VLSFT1G", "verify", "same diode family as on the Pico; SOD-123FL"),
    "R24": (YAGEO, "RC0603FR-070RL", "DNP", "D2 bypass"),
    "D3": ("Lite-On", "LTST-C171KGKT", "ok", "green 0805 (stock)"),
    "R25": (YAGEO, "RC0603FR-071KL", "ok", ""),
    "R26 R27": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "C30": ("Samsung", "CL10B104KB8NNNC", "ok", "100 nF 50 V X7R 0603 (stock)"),
    "BT1 BT2": ("Keystone", "1042", "ok", "SMT 18650 holder, not polarized, 64 mm bay for the stock plain cells (user 2026-11-27); "
                "Q1-Q4 reverse protection fitted; alternative 1042P on the same footprint"),
    "F1 F2": ("Littelfuse", "1812L260THDR", "verify", "1812, Ihold 2.6 A, Itrip 5.2 A, 8 V; tape-and-reel suffix to confirm at Digi-Key / Mouser"),
    "Q1 Q2": ("Diodes Inc.", "DMP2008UFG-13", "ok", "PowerDI3333-8 (-13 = 13 in reel, -7 restricted), 9.8 mOhm max at -2.5 V, VGSS +-8 V; pins 1-3 S, 4 G, 5 D; SOT-23 fallback PMV48XPA2"),
    "Q3 Q4": ("Diodes Inc.", "DMG2302U-7", "ok", "SOT-23, VGS(th) 0.4-1.0 V, VGSS +-8 V"),
    "R28 R29": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "R30 R31": (YAGEO, "RC0603FR-0710KL", "ok", ""),
    "R32 R33": (YAGEO, "RC0603FR-071ML", "ok", ""),
    "D4": ("Lite-On", "LTST-C171TBKT", "ok", "blue 0805 (stock; any 0805 LED colour)"),
    "R35": (YAGEO, "RC0603FR-071KL", "ok", ""),
    "R36": (YAGEO, "RC0603FR-0710KL", "ok", "CHG_STAT series"),
    "TP1": ("-", "pad only", "ok", "copper pad"),
}

# Items without a design.BOM line: refs/use, qty, description, (mfr, MPN, status, note)
EXTRA = [
    ("BT1 BT2 alt.", 0, "18650 holder, SMT, polarized, 68.9 mm bay for protected cells (alternative, same footprint)",
     ("Keystone", "1042P", "ok", "qty 0 = alternative to the 1042")),
    ("Cables", 2, "JST SH 6-pin F-F twisted cable, 10 cm, encoder color code (Pololu 4765, bought from 4project 4P-537582)",
     ("Pololu", "4765", "ok", "straight through: same color on the same pin at both ends (pin 1 green ... 6 red) -> J3/J4 pin n = encoder pin n")),
    ("Cables alt.", 0, "JST SH 6-pin single-ended cable, 12 cm + SHR-06V-S-B housing + 6 x SSH-003T-P0.2-H contacts",
     ("Pololu / JST", "4762 + SHR-06V-S-B", "ok", "alternative: crimp the free end in the same color order (pin 1 green ... 6 red)")),
    ("Cells", 2, "18650 Li-ion cell, plain (no protection PCB), flat or button top", ("any", "18650 plain", "ok",
     "user 2026-11-27; insert matched cells (within ~0.1 V); board protection: per-cell reverse FETs, BQ25606 4.208 V "
     "charge limit, TPS22810 UVLO (2.70 V option recommended), no cell temperature sensing (TS fixed); F1/F2 resettable fuses per cell")),
    ("M1 M2", 2, "30:1 Micro Metal Gearmotor HPCB 6V, extended motor shaft",
     ("Pololu", "3072", "ok", "6 V, 1100 rpm, 1.5 A stall (at 6 V); order from Pololu")),
    ("Encoders", 1, "Magnetic encoder pair kit, side-entry JST SH 6-pin, 12 CPR (2 encoders)",
     ("Pololu", "4761", "ok", "358 counts per wheel turn with the 29.86:1 gearbox; order from Pololu")),
]

# MPN -> (Digi-Key PN or "", note). Numbers carried over from Drone_1S_Pico2W (looked up Nov 2026).
DIGIKEY = {
    "74438357010": ("732-11197-1-ND", ""),
    "TPS61235PRWLT": ("296-44628-1-ND", ""),
    "BQ25606RGER": ("296-47743-1-ND", ""),
    "TPS22810DBVR": ("296-45297-1-ND", ""),
    "EG1218": ("EG1903-ND", "user, Nov 2026"),
    "GRM21BR61C106KE15L": ("490-3886-1-ND", ""),
    "CL31B226KPHNFNE": ("1276-3145-1-ND", ""),
    "103AT-2": ("4316-103AT-2-ND", "bulk"),
    "PRPC040SAAN-RC": ("S1011EC-40-ND", "bulk"),
    "SC0919": ("2648-SC0919-ND", "ordered from Mouser / Piitel (user, 2026-11-27), not Digi-Key"),
    # from the user's Digi-Key cart 2026-11-27T074756 (fabrication/DigiKey_order_2026-11-27T074756.xlsx) and doc table
    "PPPC201LFBN-RC": ("S7053-ND", ""), "BNO086": ("1888-BNO086CT-ND", ""), "FC-135 32.7680KA-A5": ("SER4103CT-ND", ""),
    "MP6550GG-Z": ("1589-MP6550GG-ZCT-ND", ""), "TPS61235PRWLR": ("296-47376-1-ND", ""),
    "USB4235-03-C": ("2073-USB4235-03-CCT-ND", ""), "AS12AP": ("360-2121-ND", ""), "SS12SDP4": ("360-2922-ND", "alternative"),
    "1812L260THDR": ("F3376CT-ND", ""), "DMP2008UFG-13": ("DMP2008UFG-13DICT-ND", ""), "DMG2302U-7": ("DMG2302U-7DICT-ND", ""),
    "MBR120VLSFT1G": ("MBR120VLSFT1GOSCT-ND", ""), "GRM21BR61E106KA73L": ("490-5523-1-ND", ""),
    "TPS22810DBVT": ("296-45304-1-ND", ""), "1042P": ("36-1042P-ND", "optional alternative"),
    "BM06B-SRSS-G-TB(LF)(SN)": ("", "Mouser 306-6BSRSSGTBLPP"),
    "1042": ("36-1042-ND", "user, Nov 2026"),
}

# Datasheet log: MPN -> [(file in Materials/bom_datasheets/ or ../ path, what it confirmed / OPEN)]
DATASHEETS = {
    "MP6550GG-Z": [("MP6550GG-Z_MPS_datasheet.pdf",
        "CONFIRMED (rev 1.0, 7/2019): QFN-12 2 x 2 mm, pins 1 IN1, 2 OUT1, 3 GND, 4 V3P3, 5 nSLEEP_LDO, 6 VCC, 7 ISET, "
        "8 OUT2, 9 VIN, 10 IN2, 11 VISEN, 12 nSLEEP_HB; VIN 1.8-22 V (abs 24), 2 A, RDS(on) HS+LS 240 mOhm; V3P3 0.47 uF, "
        "VCC 0.1-10 uF; ISET: 100 uA/A into RISET, trip at VISEN 0.5 V -> I = 5000 / R; VISEN load < 2 mA, <= 500 pF; "
        "IN1/IN2/nSLEEP internal pull-downs; other pins abs max 5 V (3.3 V GPIO OK). OPEN: package land pattern for "
        "the KD footprint."),
        ("../pololu_4733_mp6550_carrier_schematic.pdf", "reference circuit: VIN 10 uF, VCC 1 uF, V3P3 0.47 uF, ISET 2 k, VISEN 100 pF")],
    "BNO086": [("BNO086_CEVA_datasheet.pdf",
        "CONFIRMED (BNO08X datasheet, covers BNO085/BNO086): LGA-28 3.8 x 5.2 x 1.1 mm; VDD 2.4-3.6 V, VDDIO 1.65-3.6 V; "
        "PS1/PS0 select I2C / UART-RVC / UART / SPI (SPI: PS1 = PS0 = 1, PS0 then becomes WAKE); 32.768 kHz crystal across pins 26/27, CLKSEL0 low. OPEN: pad "
        "drawing for the KD footprint, pin table into the KD symbol."),
        ("../extracted/sparkfun_bno086/SparkFun_VR_IMU_Breakout_BNO086_QWIIC_Schematic_v10.pdf",
         "CONFIRMED (SparkFun schematic v10, 7/28/2023, user-supplied): pin numbers VDD 3, VDDIO 28, GND 2, GNDIO 25, CLKSEL0 10, "
         "XIN32 27, CLKSEL1 26, CAP 9, H_SA0/MOSI 17, H_SDA/MISO 20, H_SCL/SCLK 19, H_CS 18, H_INT 14, RST 11, PS0/WAKE 6, PS1 5, "
         "BOOT 4, S_SDA 16, S_SCL 15; SPI = PS0 = PS1 = 1 (table); copied into design.BNO086_PINS"),
        ("../extracted/sparkfun_bno086/SparkFun_VR_IMU_Breakout_BNO086_QWIIC.sch",
         "reference circuit (SparkFun, CC BY-SA 4.0): 100 nF VDD/VDDIO/CAP, 10 k NRST/BOOTN, PS0/PS1 jumpers to 3V3 for SPI, 4.7 k S_SDA/S_SCL, "
         "22 pF + 32.768 kHz, CLKSEL0 to GND"),
        ("BNO086_CEVA_datasheet.pdf", "crystal: 50 ppm, 12.5 pF load, fig. 1-7 shows 22 pF each side -> C1/C2 22 pF kept")],
    "TPS61235PRWLT": [("TPS61235PRWLT_TI_datasheet_SLVSCK4A.pdf", "CONFIRMED on Drone_1S_Pico2W (pinout, land pattern, values)")],
    "BQ25606RGER": [("BQ25606RGER_TI_datasheet.pdf", "CONFIRMED on Drone_1S_Pico2W (pinout, land pattern, values)")],
    "TPS22810DBVR": [("TPS22810DBVR_TI_datasheet.pdf", "CONFIRMED on Drone_1S_Pico2W (pinout, UVLO, divider option)")],
    "74438357010": [("74438357010_Wurth_datasheet.pdf", "CONFIRMED: 1 uH, Isat 6.2 A, = KiCad L_Wuerth_MAPI-4030")],
    "EG1218": [("EG1218_E-Switch_drawing.pdf",
        "CONFIRMED (drawing P040040 rev C): SPDT non-shorting, common = pin 2; 0.2 A / 30 VDC, 50 mOhm max; 3 THT pins "
        "2.50 mm pitch, 0.60 x 0.50 mm, 4.70 mm long, PCB holes 0.90 mm; body 11.6 x 4.0 x 5.4 mm, actuator 2.0 mm "
        "above the body, 2.5 mm travel; -20..+70 C. No KiCad footprint ships for it -> KD_Switches footprint."),
        ("EG_E-Switch_series_datasheet.pdf", "EG series catalog")],
    "103AT-2": [("103AT-2_Semitec_AT_thermistor.pdf", "CONFIRMED: 10 k, B 3435 K; 5.23 k / 30.9 k -> 0-60 C window")],
    "GRM21BR61C106KE15L": [("GRM21BR61C106KE15L_Murata_catalog_page.pdf", "CONFIRMED: 10 uF 16 V X5R 0805")],
    "BM06B-SRSS-TB(LF)(SN)": [("JST_SH_series_catalog.pdf",
        "CONFIRMED (SH catalog p.3): top entry, 6 circuits, A 5.0 / B 8.0 mm, depth 2.9 mm + 0.7 mm tails, height 4.25 mm, "
        "1,500 per reel; 1.0 mm pitch, 1 A per contact; KiCad JST_SH_BM06B-SRSS-TB_1x06-1MP_P1.00mm_Vertical: pads 0.6 x 1.55 "
        "at 1.0 mm, MP 1.2 x 1.8 at +-3.8 mm")],
    "USB4235-03-C": [("USB4235-03-C_GCT_drawing.pdf",
        "CONFIRMED (drawing rev A, 21 Aug 2024): USB 2.0 Type-C receptacle, vertical, SMT, 16 pin, 6.50 mm above the "
        "board, VBUS 5 A total, GND 6.25 A, 48 V. Sheet 2 land pattern: 16 pads 0.30 x 0.87 mm at 0.50 mm pitch in two "
        "staggered rows, 2 x 0.60 mm peg holes 7.50 mm apart, shell tabs 10.00 mm apart; pins A4/A9/B4/B9 VBUS, A5/B5 CC, "
        "A6/B6 D+, A7/B7 D-, A1/A12/B1/B12 + shell GND. Drawn for a 1.0 mm PCB: on 1.6 mm the 1.05 mm pegs do not protrude "
        "(all contacts SMT) - fine.")],
    "USB4120-03-C": [("USB4120-03-C_GCT_drawing.pdf", "fallback vertical USB-C 2.0, 16 contacts")],
    "1042P": [("1042P_Keystone_product_drawing.pdf",
        "CONFIRMED (drawing 1042P rev C, 9.28.26): polarized, 68.88 mm bay (protected cells), same mounting pad layout as the "
        "1042 (pads >= 7.46 x 6.47, >= 86.80 overall, holes 3.45 / 2.39 at 55.20 x 16.00)"),
        ("1042P_Keystone_18650_holders_catalog.pdf", "catalog p.29 (older pad span 86.00 min)")],
    "1042": [("1042_Keystone_product_drawing.pdf",
        "CONFIRMED (drawing 1042 rev H, 8.12.26): not polarized, 64.00 mm bay, body 77.05 x 20.65 x 14.86 mm; mounting pad layout "
        "pads >= 7.46 x 6.47 mm, >= 86.80 mm overall, holes 3.45 / 2.39 mm diagonal at 55.20 x 16.00 mm; for cells <= 67 mm "
        "with protection")],
    "1812L260THDR": [("1812L260_Littelfuse_datasheet.pdf",
        "CONFIRMED (Littelfuse 1812L series datasheet, rev 06/10/24 - user copy, same values as rev 01/10/23): 1812L260TH Ihold 2.60 A, Itrip 5.20 A, Vmax 8 V, Imax 100 A, Pd 0.8 W, "
        "time to trip 2.5 s at 8 A, R min 0.015 / R1max 0.047 Ohm; hold current derates to 2.15 A at 50 C, 1.63 A at 85 C. "
        "Pad layout (p.6): 1.78 x 3.15 mm pads, 3.45 mm gap -> KD_Power:Fuse_Littelfuse_1812L (KiCad's generic 1812 is smaller). "
        "OPEN: ordering suffix (DR = tape and reel) at the distributor.")],
    "DMP2008UFG-7": [("DMP2008UFG_Diodes_datasheet.pdf",
        "CONFIRMED: P-ch, BVDSS -20 V, VGSS +-8 V, RDS(on) max 8 mOhm @ -4.5 V, 9.8 @ -2.5 V, 13 @ -1.8 V; VGS(th) "
        "-0.4..-1.0 V; ID -11 A steady (TA 25 C); PowerDI3333-8. At 2.3 A per cell: "
        "23 mV, 0.05 W. Pinout (p.1): pins 1-3 S, 4 G, 5-8 + pad D. Suggested pad layout (p.5: C 0.65, X2 0.42, Y3 0.70, "
        "Y 3.70, X 2.37, Y1 2.25) = KiCad Package_SON:Diodes_PowerDI3333-8 (pads 1-3 S, 4 G, 5 = drain incl. fingers).")],
    "DMG2302U-7": [("DMG2302U_Diodes_datasheet.pdf",
        "CONFIRMED: N-ch SOT-23, BVDSS 20 V, VGSS +-8 V, VGS(th) 0.4-1.0 V (50 uA), RDS(on) 90 mOhm @ 4.5 V / 120 @ "
        "2.5 V - only switches a 100 k gate pull-up; reversed cell gives VGS -4.2 V, within rating.")],
    "3072": [("../pololu_micro_metal_gearmotors_datasheet_rev6-2.pdf",
        "CONFIRMED (Pololu micro metal gearmotor datasheet rev 6.2, p.45 + product page): #3072 = 30:1 (29.86:1) HPCB 6V "
        "with extended motor shaft; at 6 V: no-load 1100 rpm / 0.13 A, stall 1.5 A and 4.5 kg.mm (extrapolated), max "
        "power 1.2 W at 540 rpm / 0.82 A, max efficiency 33 % at 0.43 A; keep instantaneous torque < 20 kg.mm and "
        "continuous current <= 25 % of stall. At 5.1 V: ~935 rpm, stall ~1.28 A.")],
    "4761": [("../pololu_4760_4761_encoder_side_entry_schematic.pdf",
        "CONFIRMED (schematic + product page): JST SH 6-pin 1 GND, 2 B, 3 A, 4 VCC (2.7-18 V), 5 M2, 6 M1; 10 k pull-ups on "
        "A/B to VCC; 12 CPR")],
    "AS12AP": [("AS12AP_NKK_datasheet.pdf",
        "CONFIRMED (NKK Series AS): SPDT, non-shorting (break-before-make), logic level 0.4 VA max @ 28 V, 50 mOhm max, "
        "-30..+85 C; AS12AP = 2.5 mm actuator, straight PC pins: 3 pins at 2.54 mm, 0.8 mm PCB holes, body ~9.8 x 5.4 mm, "
        "9.1 mm tall + 2.5 mm actuator, 2.5 mm travel -> shared 3-pin 2.54 mm footprint (0.9 mm holes)")],
    "SS12SDP4": [("SS12SDP4_NKK_datasheet.pdf",
        "CONFIRMED (NKK Series SS): SS12S = SHORTING (make-before-break); gold (code 4) logic level 0.4 VA @ 28 V; top actuated, "
        "3 pins at 2.54 mm (0.6 x 0.4 mm), body 6.54 x 4.0 x 4.5 mm, -15..+60 C. With throws on BAT / GND the make-before-break "
        "would short BAT to GND -> R34 1 k in the BAT leg.")],
    "FC-135 32.7680KA-A5": [("FC-135_Epson_datasheet.pdf", "CONFIRMED (Epson FC-135): 32.768 kHz, CL 12.5 pF option, +-20 ppm option; 3.2 x 1.5 mm")],
    "PPPC201LFBN-RC": [("PPPC201LFBN-RC_Sullins_datasheet.pdf", "CONFIRMED (Sullins female headers): straight PC, .335\" (8.50 mm) insulator height, 2.54 mm pitch")],
    "MBR120VLSFT1G": [("MBR120VLSFT1G_onsemi_datasheet.pdf", "CONFIRMED (onsemi): 20 V, 1 A Schottky, very low VF, SOD-123FL; suited to battery 'OR-ing'")],
    "GRM21BR61E106KA73L": [("GRM21BR61E106KA73L_Murata_catalog_page.pdf", "CONFIRMED (Murata CAT2021 p.108): 10 uF +-10 % 25 V X5R 0805")],
    "PMV48XPA2": [("PMV48XPA2_Nexperia_datasheet.pdf", "fallback for Q1/Q2 only: SOT-23 P-FET -20 V, VGS +-12 V, RDSon 43 typ / 55 max mOhm at -4.5 V (several times the DMP2008UFG)")],
    "SC0919": [("../RPi_Pico_W_datasheet.pdf", "CONFIRMED: 51 x 21 mm, 2 x 20 pins at 2.54 mm, rows 17.78 mm"),
               ("../RPi_Pico_2_W_datasheet.pdf", "CONFIRMED: same outline and pinout (Pico 2 W upgrade)")],
}

# Ordered variants share the documents of the base part number (same die / package, different reel or plating).
for _new, _old in (("TPS61235PRWLR", "TPS61235PRWLT"), ("TPS22810DBVT", "TPS22810DBVR"),
                   ("DMP2008UFG-13", "DMP2008UFG-7"), ("BM06B-SRSS-G-TB(LF)(SN)", "BM06B-SRSS-TB(LF)(SN)")):
    if _old in DATASHEETS and _new not in DATASHEETS:
        DATASHEETS[_new] = [(f, f"(same part as {_old}) " + r) for f, r in DATASHEETS[_old]]
