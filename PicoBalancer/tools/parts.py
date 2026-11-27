"""Orderable parts for PicoBalancer: MPN per design.BOM line, distributor numbers, datasheet log.

status: "ok"      value fixed, datasheet checked (or a part already verified on Drone_1S_Pico2W)
        "verify"  MPN / variant / distributor stock still to confirm on Digi-Key or Mouser
        "TBD"     waits for a decision (see the design doc "Open decisions")
        "DNP"     footprint only
Supply chain: Digi-Key or Mouser, whichever has stock. Stock items (0603 R / C from the sample book,
0805 LEDs) are left out of the distributor CSV and listed in fabrication/BOM_stock.md.
"""

YAGEO, MURATA, TI = "Yageo", "Murata", "Texas Instruments"

# key = refs string of a design.BOM line -> (manufacturer, MPN, status, note)
MPN = {
    "U1": ("Raspberry Pi", "SC0919", "verify", "Pico WH (headers fitted) for the sockets; Pico 2 WH later"),
    "J1 J2": ("Sullins", "PPPC201LFBN-RC", "verify", "1x20 female 2.54 mm, 8.5 mm"),
    "U2": ("CEVA", "BNO086", "verify", "LGA-28; check Digi-Key / Mouser stock"),
    "Y1": ("Epson", "Q13FC1350000400", "verify", "FC-135 32.768 kHz 12.5 pF 20 ppm"),
    "C1 C2": (MURATA, "GRM1885C1H220JA01D", "ok", "22 pF C0G 0603 (stock)"),
    "C3 C4 C5": (MURATA, "GRM188R71H104KA93D", "ok", "100 nF 0603 (stock)"),
    "R1 R2": (YAGEO, "RC0603FR-0710KL", "ok", ""),
    "R3 R4": (YAGEO, "RC0603FR-0710KL", "ok", ""),
    "R5 R6": (YAGEO, "RC0603FR-074K7L", "ok", ""),
    "R7": (YAGEO, "RC0603FR-0710KL", "ok", ""),
    "U3 U4": ("Monolithic Power Systems", "MP6550GG-Z", "ok", "QFN-12 2 x 2 mm"),
    "C6 C7": (MURATA, "GRM21BR61C106KE15L", "ok", "10 uF 16 V X5R 0805"),
    "C8 C9": ("Samsung", "CL10B105KA8NNNC", "ok", "1 uF 0603 (stock)"),
    "C10 C11": ("Samsung", "CL10B474KA8NNNC", "ok", "0.47 uF 0603 (stock)"),
    "R8 R9": (YAGEO, "RC0603FR-073K9L", "TBD", "ISET, value with the motor choice"),
    "C12 C13": (MURATA, "GRM1885C1H101JA01D", "ok", "100 pF C0G 0603 (stock)"),
    "R10": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "J3 J4": ("JST", "SM06B-SRSS-TB(LF)(SN)", "ok", "mates the Pololu 4761 encoder cable"),
    "U5": (TI, "TPS61235PRWLT", "ok", ""),
    "L2": ("Wurth Elektronik", "74438357010", "ok", ""),
    "C14 C15": (MURATA, "GRM21BR61C106KE15L", "ok", ""),
    "C16 C17 C18": ("Samsung", "CL31B226KPHNFNE", "ok", "22 uF 10 V X7R 1206"),
    "R11": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "R12": (YAGEO, "RC0603FR-0749K9L", "ok", "E24 fallback 51k = 2.44 A"),
    "C19": (MURATA, "GRM188R71H103KA01D", "ok", "10 nF 0603 (stock)"),
    "J5": ("GCT", "USB4235-03-C", "verify", "vertical SMT, 6.5 mm; footprint from the GCT drawing; fallback USB4120-03-C"),
    "U6": (TI, "BQ25606RGER", "ok", ""),
    "L1": ("Wurth Elektronik", "74438357010", "ok", ""),
    "R13 R14": (YAGEO, "RC0603FR-075K1L", "ok", ""),
    "R15": (YAGEO, "RC0603FR-07226RL", "ok", "E24 fallback 240 R = 2.82 A"),
    "R16": (YAGEO, "RC0603FR-07150RL", "ok", ""),
    "R17": (YAGEO, "RC0603FR-075K23L", "ok", "E24 fallback 5.1k"),
    "R18": (YAGEO, "RC0603FR-0730K9L", "ok", "E24 fallback 30k"),
    "TH1": ("Semitec", "103AT-2", "TBD", "or R19 fixed 10k (decision open)"),
    "R19": (YAGEO, "RC0603FR-0710KL", "DNP", "TS option"),
    "C20": ("Samsung", "CL10B105KA8NNNC", "ok", "1 uF 25 V 0603 (stock)"),
    "C21 C22": (MURATA, "GRM21BR61C106KE15L", "ok", ""),
    "C23 C24": (MURATA, "GRM21BR61C106KE15L", "ok", ""),
    "C25": (MURATA, "GRM21BR61C106KE15L", "ok", ""),
    "C26": (MURATA, "GRM188R61A475KE15D", "ok", "4.7 uF 0603 (stock)"),
    "C27": (MURATA, "GRM188R71H473KA61D", "ok", "47 nF 0603 (stock)"),
    "D1": ("Lite-On", "LTST-C171KRKT", "ok", "red 0805 (stock)"),
    "R20": (YAGEO, "RC0603FR-072K2L", "ok", ""),
    "U7": (TI, "TPS22810DBVR", "ok", ""),
    "SW1": ("E-Switch", "EG1218", "ok", "user pick (Digi-Key EG1903-ND); footprint from drawing P040040"),
    "C28 C29": ("Samsung", "CL10B105KA8NNNC", "ok", "1 uF 0603 (stock)"),
    "R21 R22 R23": (YAGEO, "RC0603FR-07156KL / -07100KL / -071M27L", "DNP", "UVLO divider option"),
    "D2": ("onsemi", "MBR120VLSFT1G", "verify", "same diode family as on the Pico; SOD-123FL"),
    "R24": (YAGEO, "RC0603FR-070RL", "DNP", "D2 bypass"),
    "D3": ("Lite-On", "LTST-C171KGKT", "ok", "green 0805 (stock)"),
    "R25": (YAGEO, "RC0603FR-071KL", "ok", ""),
    "R26 R27": (YAGEO, "RC0603FR-07100KL", "ok", ""),
    "C30": (MURATA, "GRM188R71H104KA93D", "ok", "100 nF 0603 (stock)"),
    "BT1 BT2": ("Keystone", "1042P", "verify", "SMT polarized 18650 holder; peg holes from the full drawing"),
    "J6": ("Sullins", "PRPC040SAAN-RC", "DNP", "cut 4 pins from a 1x40 strip"),
    "TP1": ("-", "pad only", "ok", "copper pad"),
}

# Items without a design.BOM line: refs/use, qty, description, (mfr, MPN, status, note)
EXTRA = [
    ("Cables", 2, "JST SH 6-pin F-F twisted cable, Pololu encoder cable",
     ("Pololu", "JST SH 6-pin F-F (length TBD)", "TBD", "check pin-1-to-pin-1 mapping")),
    ("Cells", 2, "18650 Li-ion cell", ("any", "18650 (protected or not)", "TBD", "decision open")),
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
        ("../extracted/sparkfun_bno086/SparkFun_VR_IMU_Breakout_BNO086_QWIIC.sch",
         "reference circuit (SparkFun, CC BY-SA 4.0): 100 nF VDD/VDDIO/CAP, 10 k NRST/BOOTN, PS0/PS1 jumpers to 3V3 for SPI, 4.7 k S_SDA/S_SCL, "
         "22 pF + 32.768 kHz, CLKSEL0 to GND")],
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
    "SM06B-SRSS-TB(LF)(SN)": [("JST_SH_series_catalog.pdf",
        "CONFIRMED (SH catalog): 1.0 mm pitch, 1 A per contact, side entry; same layout rules as SM04B (drone) = KiCad "
        "JST_SH_SM06B-SRSS-TB")],
    "USB4235-03-C": [("USB4235-03-C_GCT_drawing.pdf",
        "CONFIRMED (drawing rev A, 21 Aug 2024): USB 2.0 Type-C receptacle, vertical, SMT, 16 pin, 6.50 mm above the "
        "board, VBUS 5 A total, GND 6.25 A, 48 V. OPEN: land pattern into the KD footprint.")],
    "USB4120-03-C": [("USB4120-03-C_GCT_drawing.pdf", "fallback vertical USB-C 2.0, 16 contacts")],
    "1042P": [("1042P_Keystone_18650_holders_catalog.pdf",
        "PARTLY (catalog p.29): 1042 / 1042P SMT single 18650, body 77.1 x 20.7 mm, pads >= 86.0 mm overall, "
        "pad >= 7.3 x 6.4 mm, holes 3.5 and 2.4 mm. OPEN: the 1042P product drawing for exact peg positions.")],
    "SC0919": [("../RPi_Pico_W_datasheet.pdf", "CONFIRMED: 51 x 21 mm, 2 x 20 pins at 2.54 mm, rows 17.78 mm"),
               ("../RPi_Pico_2_W_datasheet.pdf", "CONFIRMED: same outline and pinout (Pico 2 W upgrade)")],
}
