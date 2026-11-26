# Drone_1S_Pico2W: electronics for the 1S toothpick drone

Two boards for the 140 mm, single-18650 quad in
[OpenScad-Designs/Drones/1S_PiZero](https://github.com/arkadiraf/OpenScad-Designs/tree/main/Drones/1S_PiZero).
The flight controller is a **Raspberry Pi Pico 2 W** (RP2350 + CYW43439) on a custom module board.
It replaces the Crazyflie Bolt of the OpenSCAD design.

The design intent comes from
[Materials/Toothpick_Drone_Hardware_Design_1S_Pico_2_W.pdf](Materials/Toothpick_Drone_Hardware_Design_1S_Pico_2_W.pdf)
(2026-11-25). Its text is in `Materials/extracted/design_doc.txt`.

| Board | Folder | Size | Thickness | Carries |
|---|---|---|---|---|
| **Frame** (power board) | [Frame/](Frame/) | 117 × 117 mm, the quad frame itself | **2.0 mm** | 18650 tab pads, USB-C + BQ25606 charger, TPS22810 Pico rail switch + SPDT slide switch, 4 × TPS22997 motor switches, TPS61235P 5.1 V boost (optional), 4 × DYS XSD7A ESCs on pin headers, Pi Zero 5.1 V output, 2 × 10 header to the FC |
| **FC** (flight controller module) | [FC/](FC/) | 56 × 35.4 mm | 1.6 mm | Pico 2 W, BMI088 IMU (SPI0), BMP388 baro (I2C0), Crazyflie deck adapter for the Flow deck v2 (SPI1 + I2C0), JST-SH 4 to the Pi Zero, 2 × 10 header to the frame |

## Status: stage 1, bare boards (rev 0.1)

| Stage | Content | State |
|---|---|---|
| 1 | Outlines, holes, fixed pads, placement guides, design rules | **done** |
| 2 | Pin map and netlist in `design.py`: Pico 2 W GPIO allocation, 2 × 10 header pinout (shared by both boards) | next |
| 3 | Symbols/footprints (TPS22997 WQFN-HR, TPS22810, BQ25606, BMI088, BMP388, ...), schematics | |
| 4 | Placement, routing, pours, DRC, fab outputs (see `../AGENTS.md`) | |

![frame](docs/frame_stage1.png)
![fc](docs/fc_stage1.png)

Guides: **Dwgs.User** shows top-side parts (props, cell, Pi Zero, Pico). **Cmts.User** shows
bottom-side parts (FC module outline on the frame, Crazyflie deck rows on the FC). Edit them freely.
They don't go to the fab.

### Frame: imported from OpenSCAD

Source: `1S_PiZero.scad`, `part="pcb_outline"`, exported as `1S_PiZero_PCB_outline.dxf` (OpenScad-Designs
commit `115559d`). A copy is in `Materials/extracted/`. The committed DXF was checked against a fresh
OpenSCAD export of the same scad file: same 60 holes, same outline.

`tools/dxf_import.py` takes the largest contour as the outline (312 segments on Edge.Cuts). It fits every
other contour as a circle and snaps it to a known drill:

| Drill | Count | Became | Ref |
|---|---|---|---|
| 4.0 | 4 | motor shaft clearance, NPTH | H1–H4 (with the motor screws) |
| 2.2 | 16 | motor M2 screws, 9 mm PCD, NPTH | H1–H4 (`MotorMount_1203_M2_9mm`) |
| 2.2 | 4 | battery-cover / landing-gear M2 screws, NPTH | H_CV1–4 |
| 2.7 | 4 | FC module M2.5 screws, 30.5 mm square, NPTH | H_FC1–4 |
| 1.0 | 28 | ESC header pins, **plated**, 1.7 mm pads | J1–J4: pads 1–4 inner row (power end), 5–7 outer row (motor phases) |
| 0.8 | 4 | JST-PH holes of the Bolt-era J1 "Pi power" / J3 "Bolt power" | **dropped**: they come back as real connector footprints in stage 3 |

Plus **BT1**, the two 3 × 10 mm battery tab pads on top copper at x = ±33.6 mm (from `pcb()` in the
scad). Polarity is not set yet.

`tools/check_import.py` checks every drilled hole in the board against the DXF (within 0.01 mm, same
drill) and checks the outline segment count. Result: `IMPORT OK`, 56 holes.

Motor and ESC names: FL, FR, RR, RL (x forward to the camera, y left). In KiCad the front points right.

### FC module

* **Outline:** 56 × 35.4 mm, 2 mm corners. 35.4 mm is the Bolt's width, which fits inside the landing gear.
* **Mounting:** 4 × M2.5 (2.7 mm), 30.5 mm square, the same holes as the frame's H_FC1–4.
* **Pico 2 W** (guide only): 51 × 21 mm along x. Micro-USB at the rear edge for programming
  (the design doc keeps the charger's USB-C for charging only).
* **Antenna:** the antenna end faces forward, over a **14 × 9 mm board notch**
  (Pico 2 W datasheet §2.2.1, keep-out area: "no material should intrude", place on the board edge).
  Sources: `Materials/RPi_Pico_2_W_datasheet.pdf`, figures in `Materials/extracted/`.
* **Flow deck v2:** the guide shows the Crazyflie deck rows (2 × 1x10, 17 mm apart) on the underside.
  They run right under the Pico's castellated rows (17.78 mm apart). The deck connectors must be
  SMD, or the Pico must move. Decide this in stage 3.

## Design summary (from the design doc)

* **Power:** a 1S 18650 cell (30 A peak) feeds two paths.
  * **A, logic:** TPS22810 load switch to Pico VSYS (0.5 A). UVLO at about 2.54 V on / 2.41 V off.
    An SPDT slide switch drives EN/UVLO and only carries the signal.
  * **B, motors:** one TPS22997 per ESC, high side, about 7.5 A each.
    * ON comes from a Pico GPIO, with a 100 k pull-down: Pico off means motors off.
    * PG is open-drain with a 47 k pull-up to 3V3, read by the Pico.
    * CT sets the soft start. QOD is tied to VOUT.
* **Charger:** BQ25606 from USB-C.
  * 5.1 k pull-downs on CC.
  * R_ICHG 226 Ω for 3.0 A. R_ILIM 150 Ω for 3.2 A.
  * VSET floats (4.208 V). 10 k NTC on TS. 1 µH inductor.
  * SYS feeds the TPS22810 only. The motors stay on BAT. PG goes to the header.
* **Boost (optional):** TPS61235P, 5.1 V for the Pi Zero, enabled by a Pico GPIO (100 k pull-down).
  * Pico ↔ Pi link: JST-SH 4 on the FC (GND, TX, RX, PI_STATUS) with 1 k series resistors.
* **Header:** the frame ↔ FC header is 2 × 10, 2.54 mm. It carries VSYS, 4 × ON, 4 × PG,
  4 × DShot, BOOST_EN, CHG_PG and GND.
* **Firmware protection:**
  * The Pico reads the cell on GPIO29 (VSYS/3) and lands at 3.0–3.2 V resting.
  * The TPS22810 lockout is the hardware backstop.

### Open items carried from the doc

* [ ] Measure full-throttle current per motor (2520 props). It must stay under the XSD7A's 7 A.
* [ ] Reverse-polarity protection on the ESC power leads.
* [ ] Internal 2.54 V lockout vs the 2.70 / 3.30 V divider (R1 156 k, R2 100 k, R3 1.27 M).
* [ ] Worst-case thresholds against datasheet min/max.
* [ ] Check the TPS22997 WQFN-HR land pattern for hand assembly.

### Open items from stage 1

* [ ] OpenSCAD `pcb_t` is still 1.6 mm, and the frame here is 2.0 mm. Update the scad (it changes the
      screw lengths in its BOM) when the thickness is final.
* [ ] ESC header pin functions (pads 1–4: which is BAT+, GND, signal) need the XSD7A pad layout.
* [ ] Where the 2 × 10 header sits on both boards, and the stack height (fc_standoff is 5 mm in the scad).
* [ ] Battery tab polarity (BT1 pad 1 is at the front).
* [ ] Datasheets still to collect into `Materials/`: TPS22810, TPS22997, BQ25606, TPS61235P,
      BMI088, BMP388, Flow deck v2 and Crazyflie Bolt schematics, DYS XSD7A.

## Regenerate

```sh
cd tools
python3 dxf_import.py                 # outline + hole summary from the DXF
/usr/bin/python3 gen_pcb.py           # both boards + DRC (build/*_drc.txt), prints DRC OK
/usr/bin/python3 check_import.py      # frame holes == DXF, prints IMPORT OK
```

When the OpenSCAD frame changes, export `part="pcb_outline"` to DXF, copy it to
`Materials/extracted/1S_PiZero_PCB_outline.dxf`, update `SCAD` in `design.py`, and regenerate.

Current results: Frame 17 footprints / 58 pads, FC 4 footprints. DRC **0 violations, 0 unconnected,
0 footprint errors** on both boards. `IMPORT OK`. The boards haven't been opened in the KiCad GUI (KiCad
7.0.11 in the container). The `.kicad_pcb` files are KiCad 7 format and open in 8 and 9.
