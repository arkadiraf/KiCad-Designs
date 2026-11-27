# What is still missing (updated 27 Nov 2026)

Status of part verification: [bom_datasheets/README.md](bom_datasheets/README.md). Excluding the 19 stock
passives and LEDs, 18 parts are verified against manufacturer documents and 2 partly; 6 have no document yet
(the cable housings and contacts were added today, so their catalogs are still to come).
Parts that still need a Digi-Key number: [../fabrication/BOM_to_source.md](../fabrication/BOM_to_source.md).

## Documents still needed

| # | Part | Document | What it settles |
|---|---|---|---|
| 1 | Samsung **CL31B226KPHNFNE** (C20–C22, 22 µF 10 V X7R 1206) | Samsung datasheet / DC-bias curve (the file received was Murata's catalog) | 3 × 22 µF must stay ≥ 20 µF effective at 5.1 V for the TPS61235P |
| 2 | Sullins **PRPC040SAAN-RC** (J1–J4 ESC header strip) | Sullins drawing | pin length / plastic height under the ESC (seat height in the 3D model) |
| 3 | JST **SHR-04V-S-B / SHR-03V-S-B, SSH-003T-P0.2-H** | SH housing and contact pages (the SH catalog received covers the headers) | wire gauge, crimp tool |
| 4 | JST **PHR-2, SPH-002T-P0.5S** | PH housing and contact pages | wire gauge (24–26 AWG for 2.5 A), crimp tool |
| 5 | **DYS XSD7A** ESC | pad drawing (photos give the pad functions) | exact ESC pin map onto J1–J4 |
| 6 | Hardware (standoffs, screws, inserts) | the chosen Digi-Key parts' drawings | standoff length / hex size, insert size vs the printed bosses |

## Open decisions

- [ ] **FC socket:** Bitcraze female deck socket on 5 mm standoffs (current design, FC J1/J2 = TMM-110-01-L-S) or
      Samtec SMM-110-02-S-S on 6 mm (then J1/J2 = TMM-110-02-L-S).
- [ ] **BQ25606 SYS capacitance:** about 41 µF on SYS vs ≤ 20 µF for the charger's loop. Move the boost input to BAT
      (recommended) or keep it on SYS and test stability.
- [ ] **TPS22997 PG pull-ups (R15–R18):** on the FC, Pico internal pull-ups, or 3V3 added to the header.
- [ ] **FC additions from the Bolt:** 1 µH + 4.7 µF sensor-supply filter and 100 Ω series resistors on the DShot lines.
- [ ] **TMM-110-04-L-S-SM availability** (non-standard length at Samtec) for P1/P2.

## Received and checked

BQ25606, TPS22810, TPS22997 + RYZ0010A drawing, TPS61235P, BMI088, BMP390, Pico 2 W (datasheet, photo), Pico 2,
USB4105 (spec + SnapMagic footprint), Würth 74438357010, Semitec 103AT, APEM MA12R/TR, Omron/Aratas B3U, JST SH and
PH catalogs, Samtec SMM and TMM (TH, SM), Sullins 10483, Murata MLCC catalog, Crazyflie Bolt 1.1 schematic and
datasheet, Flow deck v2 schematic, Pi Zero 2 W brief, XSD7A images. Not used: JST SR/SZ catalog (IDC series).
