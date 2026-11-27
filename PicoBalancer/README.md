# PicoBalancer: two-wheel self-balancing robot board

One 60 × 200 × 1.6 mm PCB for a two-wheel balancing robot:
* **MCU:** Raspberry Pi Pico W (RP2040) on 2 × 20 female sockets, upgradable to a Pico 2 W (RP2350) with no board change.
* **Cells:** 2 × 18650 in parallel (1S2P) in Keystone 1042P holders, or the non-polarized 1042 on the same footprint. Each cell has its own reverse-polarity FET.
* **IMU:** BNO086 on SPI0.
* **Motors:** 2 × MP6550 H-bridges for Pololu micro metal gearmotors, each with a magnetic encoder on one JST-SH 6-pin connector.
* **Power:** the blocks are reused from [Drone_1S_Pico2W](../Drone_1S_Pico2W/): BQ25606 USB-C charger (vertical GCT USB4235), TPS22810 Pico switch with UVLO, TPS61235P 5.1 V boost.

**Design document:** [docs/PicoBalancer_Hardware_Design.pdf](docs/PicoBalancer_Hardware_Design.pdf), a PDF export of the shared
design doc (block diagram, circuits, pin map, mechanics, parts list, open decisions).
**BOM:**
* [fabrication/BOM.md](fabrication/BOM.md): every line.
* [fabrication/BOM_DigiKey.csv](fabrication/BOM_DigiKey.csv): distributor upload. Digi-Key or Mouser, whichever has stock.
* [fabrication/BOM_stock.md](fabrication/BOM_stock.md): 0603 R/C and 0805 LEDs from stock.
* [fabrication/BOM_to_source.md](fabrication/BOM_to_source.md): lines with no distributor number yet.

**Datasheets and verification:** [Materials/bom_datasheets/README.md](Materials/bom_datasheets/README.md).

## Status: stage 0 (rev 0.1)

| Stage | Content | State |
|---|---|---|
| 0 | Folder, datasheets, outline + holes from the DXF (checked against Fusion), placement guides, BOM, design doc | **done** |
| 1 | Close the open decisions (motor / ISET, cells, TS, UVLO, boost input) | next |
| 2 | Netlist in `design.py`, KD symbols/footprints (BNO086, MP6550, 1042P, USB4235, EG1218), schematic | |
| 3 | Placement, 3D review against the Fusion model, routing | |
| 4 | DRC, fab outputs | |

![stage 0 guides](docs/board_stage0.png)

## Mechanics

Sources: `Materials/extracted/PicoBalancer_PCB.dxf` and the Fusion 360 model `PicoBalancer_V01 v2`. The model was
read only, over its local MCP server, and **must not be changed without approval.**

Board coordinates: origin at the board centre, x right, y down, viewed from the holder side. The wheel end is at +y.
Fusion: `y_kicad = 121 - y_fusion`.

| Item | Position (mm) |
|---|---|
| Outline | 60 × 200 |
| Holes | 6 × Ø2.65 NPTH at x ±26, y −96 / 0 / +96, each with an 8 × 8 keep-out (`KD_Mechanical:MountingHole_2.65mm_NPTH`) |
| BT1 / BT2 (1042P) | centres (±19.0, −50.2), + contact toward the board centre |
| Channel between holders | x ±8.65, y −93.5…−6.9: vertical USB-C at the top, BQ25606 charger below, two battery-clamp holes in the middle (positions to come from Fusion) |
| Pico | centred, x ±10.5, y 14…65, micro-USB up, antenna down |
| IMU | centre bottom, about (0, 89): nearest the wheel axle |
| J3 / J4 motor connectors | bottom edge, left / right, with U3 / U4 drivers right above |

Fusion findings, reported but not changed:
* The 1042P locating pegs pass through the PCB body.
* The PCB body has no holes for those pegs.

## Key electrical choices (details in the design doc)

* **Reverse-polarity protection, one channel per cell** (Q1–Q4, R28–R33). A shared FET cannot protect parallel cells.
  * Each holder's + contact goes to BAT through its own P-FET (DMP2008UFG, 9.8 mΩ max at −2.5 V).
  * A DMG2302U turns that P-FET on only when its own cell is the right way round.
  * A reversed cell is blocked, an empty holder's contacts are dead, and charging still works through the P-FET channel.
  * This makes the non-polarized Keystone 1042 safe to use.

* **Back-feed Schottky D2** between the TPS22810 output and Pico VSYS. The Pico's own micro-USB stays usable for
  programming and cannot push current into the cells.
* **Encoder VCC = 3V3.** The Pololu encoder pulls A/B up to its VCC, and RP2040 GPIOs are not 5 V tolerant.
* **Boost EN** comes only from the Pico (GP20, 100 k pull-down), so motor power is off by default. MOTOR_EN (GP2) gates
  both MP6550 nSLEEP_HB pins the same way.
* **BNO086 on SPI0** (GP4–GP7), with INT on GP8, RST on GP9 and WAKE on GP3. PS1 and PS0/WAKE have pull-ups.
* **Slide switch:** E-Switch EG1218 (Digi-Key EG1903-ND) on the TPS22810 EN/UVLO pin, signal only.

## Regenerate

```sh
cd tools
python export_bom.py          # fabrication/BOM*.{md,csv}, passives rule, prints BOM EXPORT OK
python datasheet_index.py     # Materials/bom_datasheets/README.md
"C:/Program Files/KiCad/10.0/bin/python.exe" gen_pcb.py     # PicoBalancer.kicad_pcb, lib tables, prints IMPORT OK
"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc --output ../build/drc.txt ../PicoBalancer.kicad_pcb
```

Current results:
* `BOM EXPORT OK`: 58 lines.
* `IMPORT OK`: 6 holes match the DXF.
* DRC (KiCad 10.0.8): 0 violations, 0 unconnected.
