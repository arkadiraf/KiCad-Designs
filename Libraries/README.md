# Libraries – shared KiCad symbols and footprints

Parts used by more than one design live here, so every board in this repository uses the same
checked symbol and land pattern. All files are **generated** by `tools/gen_lib.py`. Don't edit them by
hand: change the generator and re-run it.

```sh
cd Libraries/tools && python3 gen_lib.py
```

KiCad 7 format (it opens in 8 and 9). Where KiCad's stock library already has the right footprint,
the symbol points at it instead of duplicating it.

## Contents

| Library | Part | Symbol pins | Footprint | Used by |
|---|---|---|---|---|
| `KD_Power` | **BQ25606** 1S 3 A charger | 25 | stock `Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias` | Drone_1S frame |
| `KD_Power` | **TPS22997** 10 A load switch | 10 | `KD_Power:Texas_RYZ0010A_WQFN-HR-10_2x1.5mm_P0.5mm` | Drone_1S frame (×4) |
| `KD_Power` | **TPS22810DBV** 2 A load switch with UVLO | 6 | stock `Package_TO_SOT_SMD:SOT-23-6` | Drone_1S frame |
| `KD_Power` | **TPS61235P** 5.1 V boost | 9 | `KD_Power:Texas_RWL_VQFN-HR-9_2.5x2.5mm_P0.5mm` | Drone_1S frame (optional) |
| `KD_Sensors` | **BMI088** IMU | 16 | `KD_Sensors:Bosch_LGA-16_3x4.5mm_P0.5mm` | Drone_1S FC |
| `KD_Sensors` | **BMP388** barometer | 10 | `KD_Sensors:Bosch_LGA-10_2x2mm_P0.5mm` | Drone_1S FC |
| `KD_Modules` | **Raspberry Pi Pico 2 W**, castellated SMD (plus the underside TP1–3 USB, TP6 BOOTSEL and SWD pads) | 47 | `KD_Modules:RPi_Pico_2_W_SMD_Castellated` | Drone_1S FC |
| `KD_Connectors` | **Bitcraze female deck connector** 1×10 2.00 mm SMD (Crazyflie decks) | stock `Connector_Generic:Conn_01x10` | `KD_Connectors:Bitcraze_FemaleDeck_1x10_P2.00mm_SMD` | Drone_1S frame |

## Using the libraries in a project

Add the libraries to the project's `sym-lib-table` / `fp-lib-table` through `${KIPRJMOD}`. Here is the
entry for a project folder two levels below the repository root (e.g. `Drone_1S_Pico2W/Frame/`):

```
(lib (name "KD_Power")(type "KiCad")(uri "${KIPRJMOD}/../../Libraries/KD_Power.pretty")(options "")(descr ""))
```

From Python, `gen_lib.lib_table_entries("<relative path>")` returns all of the table lines.
`Drone_1S_Pico2W/tools/gen_libs.py` uses it. Generators that load footprints with `pcbnew.FootprintLoad`
take `KD_*` libraries from this folder (see `load_fp()` in `Drone_1S_Pico2W/tools/gen_pcb.py`).

## Verification

The TI and Bosch datasheets could not be downloaded from the build environment. Each part was
therefore cross-checked against **independent open-source KiCad libraries** instead. Pins were
compared by number and name, and pads by centre and size, with `kicompare`-style scripts. The
generated symbols were then compared back against a reference symbol: every pin number and
function matches, and the only differences are names (`~{PG}` vs `PG_N`, `EP` vs `PAD`). The sources
are listed in [sources/SOURCES.md](sources/SOURCES.md).

| Part | Pinout sources (agree) | Land pattern sources | Status |
|---|---|---|---|
| BQ25606 | **TI datasheet SLUSCK6C (rev C)**, plus381-robotics, Y2K-x/psxpress, oliver-nederal/OpenRide-PCB, Decktrix-Lab | KiCad stock RGE0024H = TI land pattern RGE0024H (pad pitch and positions; KiCad pads longer outward) | **confirmed** against the datasheet |
| TPS22997 | girishji/tmr-keyboard, emaneric/EN_Designs, teehee567/Aevia (3/3) | teehee567 (cites TI MPQF651A) = girishji: same pad centres | **TO CHECK** against TI MPQF651A. Fine pitch for hand assembly (doc open item) |
| TPS22810DBV | official KiCad 9 `Power_Management:TPS22810DBV` (KiCad 7 has only the DRV/WSON variant) | stock SOT-23-6 | **TO CHECK** against the datasheet |
| TPS61235P | Redherring32/Xbox-Portable, k5utd/Cobalt-Cowboy, unsurv/unsurv-offline (3/3) | asukiaaa (cites the TPS61235P datasheet) = Redherring32/TinyTendo = unsurv: same pad centres. Sizes from asukiaaa (the others make the power pads 0.14 mm wider) | **TO CHECK** against the datasheet |
| BMI088 | **Bitcraze Crazyflie Bolt 1.1 schematic (rev H)**, murexrobotics, bit-bots, ArduPilot NxtPX4v2 (ground names 4 GND_IO / 6 GND as the Bolt) | ArduPilot NxtPX4v2 = bit-bots = KiCad generator (BST-BMI088-DS000-19) | pin numbers confirmed; pad-1 corner **TO CHECK** (Bosch drawing) |
| BMP388 | Bitcraze Bolt 1.1 schematic, leelili444, Caped-Crussader/VENDETTAFC, fdiwth/tvc-drone, ArduPilot NxtPX4v2 (5/5) | OpenAXES = KiCad generator (BST-BMP388-DS001) | good |
| Pico 2 W | Pico 2 W datasheet §2.1 (same pinout as Pico / Pico W) | datasheet Fig. 5; TP1–3 / TP6 and SWD names from the module's bottom silkscreen (photo); TP1–3 also = Pico 2 datasheet Fig. 5 | good (TP positions corrected after the photo) |
| Bitcraze female deck | — | Bitcraze female deck connector drawing (bitcraze/hardware) | good |

Before ordering boards, confirm each **TO CHECK** item against the manufacturer datasheet, and record
the result here.

## Adding a part

1. Find at least two independent sources for the pinout and the land pattern (open-source KiCad
   libraries, the manufacturer's land pattern, the KiCad generator). Record them in
   `sources/SOURCES.md`.
2. Add a `sym_*()` and/or `fp_*()` function to `tools/gen_lib.py` and register it in `SYMBOLS` /
   `FOOTPRINTS`. Write the source comparison in the function's docstring.
3. Run `gen_lib.py` and load the footprint with `pcbnew.FootprintLoad`. Plot the symbol with
   `kicad-cli sym export svg` and look at it.
4. Add the part to the tables above.
