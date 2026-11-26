# Pico Alvik Adapter

Adapter board that lets a **Raspberry Pi Pico W** replace the **Arduino Nano ESP32**
as the main controller of the **Arduino Alvik** robot (AKX00066).

* The Pico W is soldered **flat on the top side by its castellated edge pads**,
  with no pin headers between the boards.
* The bottom side carries two **1x15 2.54 mm SMD male headers in the Arduino Nano
  footprint**. They plug into the Alvik's Nano socket in place of the Nano ESP32.
* Every Nano pin the Alvik uses (UART, BOOT0, NRST, NANO_CHK, ROBOT_CHK, I2C,
  VIN, 3V3, GND) goes to a matching Pico pin: UART0 for the STM32 link and I2C1
  for the I2C bus. Nine spare Nano pins are wired as well.
* The micro-USB connector of the Pico sits at the same end as the Nano's USB-C,
  so it stays reachable through the Alvik's rear opening.

Designed in KiCad (files saved in KiCad 7 format; they open in KiCad 7, 8 and 9).

![Board render](fabrication/docs/Pico_Alvik_Adapter_render.png)

| | |
|---|---|
| Board size | 24.0 x 51.0 mm, 2 layers, 1.6 mm FR4 |
| Pico W | 21 x 51 mm module, top side, castellated SMD |
| Nano headers | 2x 1x15 2.54 mm SMD male, bottom side, rows 15.24 mm apart |
| Antenna | 14 x 9 mm board notch under the Pico W antenna (datasheet keep-out) |

## Project layout

```
Pico_Alvik_Adapter.kicad_pro / .kicad_sch / .kicad_pcb   KiCad project
PicoAlvik.kicad_sym, PicoAlvik.pretty/                   project-local symbols & footprints
sym-lib-table, fp-lib-table                              library tables (use ${KIPRJMOD})
tools/                                                   generator scripts (design.py is the single source of truth)
firmware/pinout_definitions_pico.py                      Alvik MicroPython pin map for the Pico W
fabrication/                                             gerbers, drill, BOM, position file, PDFs, renders
Materials/                                               datasheets / pinouts / schematics used for the design
```

## Pin mapping

Nano header pin numbers use the classic Nano numbering (1 = D1/TX ... 30 = VIN).

**Pins used by the Alvik** (from Arduino's `arduino-alvik-mpy` library, `pinout_definitions.py` and `uart.py`, plus the
Alvik datasheet block diagram; copies in `Materials/extracted/`):

| Nano pin | J1 | Pico GPIO | U1 pin | Alvik function | Pico peripheral |
|---|---|---|---|---|---|
| D1/TX1 | 1 | GP16 | 21 | UART TX -> STM32 RX (460800 baud) | UART0 TX |
| D0/RX0 | 2 | GP17 | 22 | UART RX <- STM32 TX | UART0 RX |
| D2 | 5 | GP20 | 26 | STM32 BOOT0 | |
| D3 | 6 | GP21 | 27 | STM32 NRST | |
| D4 | 7 | GP22 | 29 | NANO_CHK (EXT_CHK) | |
| A4/SDA | 23 | GP6 | 9 | I2C SDA (Qwiic / Grove, BMS, IMU...) | I2C1 SDA |
| A5/SCL | 24 | GP7 | 10 | I2C SCL | I2C1 SCL |
| A6 | 25 | GP8 | 11 | ROBOT_CHK (input) | |
| 3V3 | 17 | 3V3(OUT) | 36 | +3V3_EXT supply of the Alvik | via JP2 (bridged) |
| VBUS/VUSB | 27 | VBUS | 40 | Alvik power / charge input (USB 5V) | direct |
| VIN | 30 | VSYS | 39 | Alvik power output to the controller | D1 Schottky (opt. 0 Ω) |
| GND | 4, 29 | GND | 3,8,13,18,23,28,33,38 | | |
| RST | 3 | RUN | 30 | (not used by the Alvik) | via JP3 (open) |

**Spare Nano pins** (the Alvik leaves these unconnected). The ones that route cleanly are wired anyway:

| Nano pin | J1 | Pico GPIO | U1 pin | Note |
|---|---|---|---|---|
| D5 | 8 | GP26 | 31 | ADC0 |
| D6 | 9 | GP27 | 32 | ADC1 |
| D7 | 10 | GP28 | 34 | ADC2 |
| D13 | 16 | GP1 | 2 | |
| A0 | 19 | GP2 | 4 | |
| A1 | 20 | GP3 | 5 | |
| A2 | 21 | GP4 | 6 | |
| A3 | 22 | GP5 | 7 | |
| A7 | 26 | GP9 | 12 | |

Not connected: Nano D8–D12, B0, B1. Pico GP0, GP10–GP15, GP18, GP19,
ADC_VREF and 3V3_EN.

Each group is assigned in the same order on both sides, so its tracks never cross. The Nano-side
order is kept on the Pico's right edge (TX/RX/D2–D4) and left edge (A4–A6).

## Power design

How the Alvik uses the controller's power pins:

* **VBUS/VUSB (Nano pin 27):** the Alvik's power / battery-charge **input**. On a Nano this pin is raw
  USB 5V; the Nano schematic shows the USB-C VBUS pins tied straight to the `VUSB` header pin.
* **VIN (Nano pin 30):** the Alvik's power **output** to the controller. On a Nano, VIN is the input of
  its MP2322 regulator.

The adapter:

| Situation | Path |
|---|---|
| USB plugged into the Pico | Pico VBUS -> **Nano VUSB pin, direct** -> Alvik (powers the robot / charges the 18650) |
| | Pico VBUS -> Pico on-board Schottky -> VSYS (powers the Pico) |
| USB unplugged | Alvik VIN output -> **D1** -> VSYS (Alvik powers the Pico) |
| Both present | VSYS is diode-OR'ed (D1 / Pico diode); the higher source supplies the Pico |

* **D1: Nexperia PMEG6020ER** (2 A / 60 V Schottky, SOD-123W, anode = VIN). It stops the USB-derived
  VSYS (about 4.7 V) from back-feeding the Alvik's VIN output, in case the Alvik has no diode of its own
  there. Blocking that direction costs nothing, because the Alvik takes its power from VUSB, not VIN.
* **Option: 1206 0 Ω on the D1 pads.** This removes the ~0.35 V drop and matches a Nano exactly, where
  VIN is the regulator input with no diode and USB reaches VIN through the Nano's own PMEG6020. Only fit
  it if you know the Alvik's VIN output tolerates that.
* Charge current flows from the Pico's micro-USB straight to the VUSB pin. It does not pass through the
  Pico's 1 A on-board diode, or through D1.
* **VSYS range is 1.8–5.5 V.** The Alvik VIN output minus the D1 drop is inside that range.
* **JP2 (bridged):** Pico 3V3(OUT) -> Nano 3V3 pin. On the Nano, 3V3 is the output of its regulator,
  and on the Alvik it feeds `+3V3_EXT` (the I2C switch supply). Keep the 3V3 load under 300 mA. If you
  ever measure about 3.3 V on the Alvik's 3V3 socket pin with no controller fitted, cut JP2.
* **JP3 (open):** optional, Nano RST -> Pico RUN.
* C1: 10 µF on VSYS.

**Bring-up check:** with the adapter removed and the Alvik switched on, measure the Alvik's Nano socket.
VIN (pin 30) should be ≤ 5.5 V. VUSB (pin 27) and 3V3 (pin 17) should be about 0 V.

## Mechanical notes

* The SMD headers keep the top copper flat under the Pico W, because Nano rows (15.24 mm) and
  Pico rows (17.78 mm) overlap and through-hole joints would short against the Pico's pins.
* Copper is kept out from under the Pico W test points TP1–TP6 and the SWD pads (datasheet §2.2).
  Vias are tented.
* The board is 24 mm wide (Nano: 18 mm). Check the clearance inside the Alvik's
  top cover before ordering.
* Bottom-side parts (C1, D1, jumpers) sit between the header rows and are at most about 1.2 mm high.
* Use male headers with a standard 2.54 mm pin (about 6 mm mating length). Recommended stack:
  SMD header, e.g. Samtec TSM-115-01-x-SV or any generic 1x15 SMD 2.54 mm male header.

## Firmware

`firmware/pinout_definitions_pico.py` is a Pico W version of the Alvik library's
`pinout_definitions.py`. It also lists the other changes the RP2040 port needs:
UART0 on GP16/GP17, I2C1 on GP6/GP7, and a single LED instead of an RGB LED.

## Regenerating the design

The schematic, libraries and PCB are produced by the scripts in `tools/`
from `tools/design.py`:

```sh
cd tools
python3 gen_libs.py                 # PicoAlvik.kicad_sym + PicoAlvik.pretty
python3 gen_schematic.py            # Pico_Alvik_Adapter.kicad_sch
kicad-cli sch export netlist -o ../build/net.net ../Pico_Alvik_Adapter.kicad_sch
python3 check_netlist.py ../build/net.net     # schematic == design.py ?
/usr/bin/python3 gen_pcb.py place   # placement, outline, keep-outs (+ .dsn for Freerouting)
/usr/bin/python3 gen_pcb.py geom    # geometry for the router
python3 router.py                   # 2-layer A* grid router -> build/routes.json
/usr/bin/python3 gen_pcb.py finish  # import routes, GND pours, zone fill, DRC report
bash export_fab.sh                  # gerbers, drill, BOM, PDFs
python3 render_board.py             # fabrication/docs/Pico_Alvik_Adapter_render.png
```

Status of the checked-in board: all nets routed, **KiCad DRC: 0 violations, 0 unconnected
pads** (`build/` is regenerated and not committed). KiCad 7's command line has no ERC, so the
schematic is verified with `check_netlist.py`, which compares KiCad's exported netlist to `design.py`.
Running ERC once in the KiCad GUI is still worthwhile.

`gen_pcb.py place` also writes `build/Pico_Alvik_Adapter.dsn`. If you prefer Freerouting,
route that file, save the `.ses` as `build/Pico_Alvik_Adapter.ses`, delete
`build/routes.json`, and run `gen_pcb.py finish`.
