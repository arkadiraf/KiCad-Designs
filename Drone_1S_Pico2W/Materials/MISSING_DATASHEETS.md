# Datasheets still needed for validation

These manufacturer sites are blocked from the build container. Until the PDFs are here, the parts
are checked only against open-source KiCad libraries (see `../../Libraries/README.md`). Drop each PDF
into `Materials/` under the file name given. Each item lists what it validates.

## Priority 1: blocks schematic values and land-pattern sign-off

| # | Document | Save as | Validates | Link |
|---|---|---|---|---|
| 1 | TI **BQ25606** datasheet | `bq25606.pdf` | RGE pinout and land pattern; K_ICHG / K_ILIM (R3 226 Ω, R4 150 Ω); TS divider for the 103AT (R5/R6); inductor (L1) and capacitor values; VSET; D+/D− detection; STAT drive | ti.com/lit/ds/symlink/bq25606.pdf |
| 2 | TI **TPS22997** datasheet | `tps22997.pdf` | pinout; VBIAS range (tie to BAT?); CT vs rise time (C14–C17); PG open-drain levels; QOD; current and thermal limits at ~7.5 A | ti.com/lit/ds/symlink/tps22997.pdf |
| 3 | TI **RYZ0010A** package / land pattern (WQFN-HR-10) | `mpqf651a.pdf` | the `KD_Power:Texas_RYZ0010A...` pads; hand-assembly fit (doc open item) | ti.com/lit/ml/mpqf651a/mpqf651a.pdf |
| 4 | TI **TPS22810** datasheet | `tps22810.pdf` | DBV (SOT-23-6) pinout; internal UVLO 2.54 / 2.41 V vs the R8–R10 divider; EN thresholds for the slide switch; CT; QOD | ti.com/lit/ds/symlink/tps22810.pdf |
| 5 | TI **TPS61235P / TPS61236P** datasheet (incl. RWL package drawing) | `tps61235p.pdf` | RWL pinout and land pattern; inductor (L2); input/output capacitors (C18–C22); CC / current-limit resistor (R20, ~2.5 A); INACT and FB pin use; EN levels | ti.com/lit/ds/symlink/tps61235p.pdf |
| 6 | Bosch **BMI088** datasheet | `BST-BMI088-DS001.pdf` | pad-1 corner (pin numbers confirmed by the Bolt schematic); LGA-16 land pattern; PS strap for SPI; decoupling; accel SPI start-up | bosch-sensortec.com (BMI088 product page, Downloads) |
| 7 | Bosch **BMP388** datasheet | `BST-BMP388-DS001.pdf` | LGA-10 land pattern; CSB/SDO strapping (I2C address 0x77); decoupling | bosch-sensortec.com (BMP388 product page, Downloads) |
| ~~8~~ | ✅ **received** – Bitcraze **Flow deck v2** schematic | `flow-deck-v2-schematic.pdf` | which deck pins it uses: supply (VCC / 3V3 / VCOM), the PMW3901 CS pin, the I2C and SPI pins; PMW3901 / VL53L1x running from 3.3 V | bitcraze.io (Flow deck v2 product page) / github bitcraze hardware |

## Priority 2: reference circuits and mechanical fit

| # | Document | Save as | Validates |
|---|---|---|---|
| ~~9~~ | ✅ **received** – Bitcraze **Crazyflie Bolt 1.1** schematic | `crazyflie-bolt-1.1-schematic.pdf` | BMI088 / BMP388 reference circuits (analog supply filter, interrupt wiring) |
| 10 | ◐ **partly** (vendor images: size, ratings, pad silk) – **DYS XSD7A** ESC datasheet or pad drawing | `dys-xsd7a.pdf` | ESC header J1–J4 pin functions (BAT+, GND, signal), 7 A continuous rating, DShot support |
| 11 | **2.00 mm male SMD header** datasheet (the FC J1/J2 and P1/P2 part) | `header-2mm-smd.pdf` | plastic and pin heights against the 5 mm standoff and the Bitcraze socket (2.1 mm) |
| ~~12~~ | ✅ **received** (photo; TP positions fixed) – **Pico 2 W underside**: a photo or drawing of the bottom silkscreen (not covered by the datasheet) | `pico2w-bottom.jpg` | TP1/TP2/TP3 order (GND, USB DM, USB DP) and SWD pad order (SWCLK, GND, SWDIO) |
| ~~13~~ | ✅ **received** (5 V 2.5 A) – Raspberry Pi **Zero 2 W** product brief | `pi-zero-2w-product-brief.pdf` | 5 V supply current, so the boost can be sized; GPIO header 5 V pins |

## Priority 3: stock footprints to confirm

| # | Document | Save as | Validates |
|---|---|---|---|
| 14 | GCT **USB4105-GF-A** drawing | `usb4105.pdf` | J10 footprint (stock `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal`) |
| 15 | C&K **PCM12** slide switch drawing | `pcm12.pdf` | SW1 footprint and actuator position at the frame edge |
| 16 | Coilcraft **XAL4020** datasheet | `xal4020.pdf` | 1 µH part: Isat ≥ 3.6 A (charger), boost inductor current; footprint |
| 17 | Semitec **103AT-2** NTC datasheet | `103at.pdf` | R–T table for the BQ25606 TS divider (with item 1) |
| 18 | JST **SH** (SM03B / SM04B-SRSS-TB) and **PH** (S2B-PH) drawings | `jst-sh.pdf`, `jst-ph.pdf` | J7, J8, J9 footprints and heights |

Received so far: the Crazyflie Bolt 1.1 schematic and datasheet, the Flow deck v2 schematic, the Pi Zero
2 W product brief, the Pico 2 datasheet, a Pico 2 W underside photo, and XSD7A images. Validation
results are in the README ("Validation against uploaded documents").

Already here before that: the design doc, the Pico 2 W datasheet, and the Bitcraze deck connector / Flow deck
mechanical drawings (`extracted/bitcraze/`).
