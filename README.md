# KiCad-Designs
KiCad Design Projects

| Project | Description |
|---|---|
| [Pico_Alvik_Adapter](Pico_Alvik_Adapter/) | Raspberry Pi Pico W carrier in Arduino Nano form factor, replaces the Nano ESP32 in the Arduino Alvik robot |
| [Drone_1S_Pico2W](Drone_1S_Pico2W/) | 1S toothpick drone: 2 mm PCB frame / power board (from the OpenSCAD 1S_PiZero frame) and a Pico 2 W flight-controller module. Stage 1: bare boards |

| [Libraries](Libraries/) | Shared KiCad symbols and footprints for reuse across designs (KD_Power: BQ25606, TPS22997, TPS22810DBV, TPS61235P; KD_Sensors: BMI088, BMP388; KD_Modules: Pico 2 W; KD_Connectors: Bitcraze deck socket) |

## Design rules (all projects)

* **Passives:** chip resistors and capacitors are **0603**. Bulk capacitors (10 µF and up, or where the
  voltage rating needs a bigger case) are **0805 or 1206**. No 0402 or smaller: the boards are
  hand-assembled. Exceptions (e.g. a current-sense or power resistor in a larger case) must be
  stated next to the part in the project's `design.py`.
* **LEDs:** 0805 (`LED_SMD:LED_0805_2012Metric`). `Drone_1S_Pico2W/tools/check_bom.py`
  enforces this rule. Copy it into new projects.
* **Shared parts:** custom symbols and footprints go in [Libraries](Libraries/), not project-local
  libraries, so later designs can reuse them.

Workflow for new projects (design-as-code generators, checks, manufacturing outputs): see [AGENTS.md](AGENTS.md).
