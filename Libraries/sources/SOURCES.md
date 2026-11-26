# Sources for the shared library parts

The third-party files themselves are not copied into the repository, because their licences vary.
Each file is listed below as `owner/repo` and path on GitHub (default branch, fetched 2026-11). The
pin and pad comparison results are in `../README.md` and in the docstrings of `../tools/gen_lib.py`.

## BQ25606 (RGE VQFN-24)

| Kind | Repository | Path |
|---|---|---|
| symbol | plus381-robotics/kicad-parts | `symbols/Plus381_Power.kicad_symdir/BQ25606RGER.kicad_sym` |
| symbol | Y2K-x/psxpress | `CAD/PCB/psxpress-pms/lib/BQ25606RGER.kicad_sym` |
| symbol | oliver-nederal/OpenRide-PCB | `Symbols/BQ25606RGER.kicad_sym` |
| symbol | Decktrix-Lab/decktrix | `hardware/MAIN_PCB/lib/BQ25606RGER.kicad_sym` |
| footprint | plus381-robotics/kicad-parts | `footprints/Plus381_Power.pretty/RGE0024H.kicad_mod` |
| footprint | Y2K-x/psxpress | `CAD/PCB/psxpress-pms/lib/BQ25606RGER.pretty/QFN50P400X400X100-25N-D.kicad_mod` |
| footprint | SimonBrenninger/smartWatch | `pcb/lib/LIB_BQ25606RGET/KiCad/QFN50P400X400X100-25N.kicad_mod` |
| footprint (used) | KiCad 7 stock | `Package_DFN_QFN.pretty/Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias` |

Agreed pinout: 1 VAC, 2 NC, 3 D+, 4 D−, 5 STAT, 6 OTG, 7 /PG, 8 ILIM, 9 /CE, 10 ICHG, 11 TS, 12 VSET,
13–14 BAT, 15–16 SYS, 17–18 GND, 19–20 SW, 21 BTST, 22 REGN, 23 PMID, 24 VBUS, 25 thermal pad.

## TPS22997 (RYZ0010A WQFN-HR-10, 2 × 1.5 mm)

| Kind | Repository | Path |
|---|---|---|
| symbol | girishji/tmr-keyboard | `hardware/nRF54LM20_TMR2615/tmr-symbols.kicad_sym` |
| symbol | emaneric/EN_Designs-KiCad-Lib | `Symbols/EN_Designs-Symbols.kicad_sym` |
| symbol | teehee567/Aevia | `hardware/v2_pcb/open-race-v2.kicad_sym` |
| footprint | teehee567/Aevia | `hardware/v2_pcb/noob.pretty/Texas_RYZ0010A_WQFN-HR-10_2x1.5mm_P0.5mm.kicad_mod` |
| footprint | girishji/tmr-keyboard | `hardware/nRF54LM20_TMR2615/tmr-footprints/tps22997.kicad_mod` |

Agreed pinout: 1 VBIAS, 2–3 VIN, 4 PG, 5 GND, 6 QOD, 7–8 VOUT, 9 CT, 10 ON.

## TPS22810 (DBV SOT-23-6)

| Kind | Repository | Path |
|---|---|---|
| symbol | deepin-community/kicad-symbols (mirror of the official KiCad 9 library) | `Power_Management.kicad_symdir/TPS22810DBV.kicad_sym` |

Pinout: 1 VIN, 2 GND, 3 EN/UVLO, 4 CT, 5 QOD, 6 VOUT. (The KiCad 7 `TPS22810DRV` WSON-6 has a different
pinout. Don't swap packages without changing the symbol.)

## TPS61235P (RWL VQFN-HR-9, 2.5 × 2.5 mm)

| Kind | Repository | Path |
|---|---|---|
| symbol | Redherring32/Xbox-Portable | `PSU/Xbox-PMS.kicad_sym` |
| symbol | k5utd/Cobalt-Cowboy | `Hardware/KiCAD/Cobalt-Cowboy.kicad_sym` |
| symbol | unsurv/unsurv-offline | `hardware/main/unsurv_offline_pcb_symbols.kicad_sym` |
| footprint (sizes used) | asukiaaa/asukiaaa-kicad-footprints.pretty | `TPS6123x.kicad_mod` |
| footprint | Redherring32/TinyTendo | `Hardware/ChargeBoost/ChargeBoost.pretty/CONV_TPS61235PRWLT.kicad_mod` |
| footprint | unsurv/unsurv-offline | `hardware/main/unsurv_offline_pcb_footprints.pretty/cursed_TI-QFN9_TPS61235.kicad_mod` |

Agreed pinout: 1 PGND, 2 SW, 3 VIN, 4 CC, 5 AGND, 6 FB, 7 EN, 8 INACT, 9 VOUT.

## BMI088 (LGA-16) and BMP388 (LGA-10)

| Kind | Repository | Path |
|---|---|---|
| symbol | murexrobotics/electrical | `library/BMI088/BMI088.kicad_sym` |
| symbol | bit-bots/bitbots_imu_dxl | `electronics/imu_module/lib/BMI088.kicad_sym` |
| symbol | ArduPilot/Schematics | `HKUST-UAV-Group/NxtPX4v2/project_lib/NxtPX4_Symbol.kicad_sym` (BMI088 + BMP388) |
| symbol | leelili444/Hardware | `library/symbols/BMP388.kicad_sym` |
| symbol | Caped-Crussader/VENDETTAFC | `VFC/Library/BMP388/BMP388.kicad_sym` |
| symbol | fdiwth/tvc-drone | `resources/pcb/libs/symbols/QFN_BMP388_BOS.kicad_sym` |
| footprints | see `Drone_1S_Pico2W/Materials/extracted/sensor_footprints/` (ArduPilot, KiCad generator, OpenAXES, atopile) | |

BMI088: 1 INT2, 2 NC, 3 VDD, 4 GNDA, 5 CSB2, 6 GNDIO, 7 PS, 8 SCK, 9 SDI, 10 SDO2, 11 VDDIO, 12 INT3,
13 INT4, 14 CSB1, 15 SDO1, 16 INT1.
BMP388: 1 VDDIO, 2 SCK, 3 VSS, 4 SDI, 5 SDO, 6 CSB, 7 INT, 8 VSS, 9 VSS, 10 VDD.

## Raspberry Pi Pico 2 W, Bitcraze deck connector

* Pico 2 W datasheet (RP-008304-DS): `Drone_1S_Pico2W/Materials/RPi_Pico_2_W_datasheet.pdf`. Pinout in §2.1,
  SMT footprint in Fig. 5 (`Materials/extracted/pico2w_smt_footprint.png`).
* Bitcraze female deck connector drawing: `Drone_1S_Pico2W/Materials/extracted/bitcraze/` (see its
  SOURCES.md).
