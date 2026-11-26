# AGENTS.md – KiCad-Designs workflow

Guide for coding agents (and humans) starting or changing a hardware project in this repository.
The reference implementation is **`Pico_Alvik_Adapter/`**. Copy its `tools/` folder as the template
for a new board, and read its `README.md` for a complete worked example.

## 1. Principles

1. **Design as code.** One Python file (`tools/design.py`) is the single source of truth: pin map,
   netlist, parts, board geometry. The symbol and footprint libraries, schematic, PCB and firmware
   pin maps are *generated* from it, so they can't disagree. Don't hand-edit generated files and
   then regenerate over them. Change `design.py` or the generator instead.
2. **Every claim needs a source.** Pinouts, power paths, footprints and keep-outs come from
   datasheets and schematics, not memory. Store the sources in `<Project>/Materials/`, with excerpts
   (cropped figures, copied source files) in `Materials/extracted/`. When a source is missing or
   ambiguous, say so, ask the user, and design so both readings work (solder jumpers, DNP options).
3. **Verify before you commit.** Each stage has a check (section 4). Report the real result
   (counts, DRC numbers), and say plainly what could *not* be verified, such as a test not run on
   hardware or a site that couldn't be fetched.
4. **The user decides the electrical intent.** When the user knows how the target system behaves
   (e.g. "the Alvik takes power on VUSB, VIN is its output"), follow it, explain the consequences,
   and keep the alternative as a footprint option (e.g. diode vs 0 Ω on the same pads).

## 2. Project layout (per board)

```
<Project>/
  README.md                       overview, pin map, power design, mechanical notes, how to regenerate
  <Project>.kicad_pro/.kicad_sch/.kicad_pcb    generated KiCad project (KiCad 7 format, opens in 8/9)
  <Lib>.kicad_sym, <Lib>.pretty/  project-local symbols/footprints (generated)
  sym-lib-table, fp-lib-table     use ${KIPRJMOD}
  Materials/                      datasheets, pinouts, schematics; extracted/ = figures & excerpts
  tools/                          design.py + generators + checks (see section 3)
  firmware/                       pin maps / port kits for the target software, checked against design.py
  fabrication/                    generated production outputs (committed)
  build/                          scratch: netlists, DRC report, router files (git-ignored)
```

## 3. Pipeline (`<Project>/tools/`)

| Step | Command | Output / check |
|---|---|---|
| 1. Libraries | `python3 gen_libs.py` | `<Lib>.kicad_sym`, `<Lib>.pretty/*.kicad_mod`, lib tables |
| 2. Schematic | `python3 gen_schematic.py` | `.kicad_sch`; parts placed with net labels on every pin, notes, title block |
| 3. Netlist check | `kicad-cli sch export netlist -o ../build/net.net ../<P>.kicad_sch && python3 check_netlist.py ../build/net.net` | must print `NETLIST OK` |
| 4. Place PCB | `/usr/bin/python3 gen_pcb.py place` | `.kicad_pro` (rules, net classes), placed board, outline, keep-outs, silkscreen, `.dsn` |
| 5. Router input | `/usr/bin/python3 gen_pcb.py geom` | `build/geometry.json` |
| 6. Route | `python3 router.py` | `build/routes.json`; prints failed nets per pass (GND is completed by pours) |
| 7. Finish | `/usr/bin/python3 gen_pcb.py finish` | re-places, imports routes, GND pours both layers, zone fill, `build/drc_report.txt` |
| 8. Firmware check | `python3 check_firmware.py` | firmware pin map == `design.py` |
| 9. Outputs | `bash export_fab.sh` (from `<Project>/`) | fab zips, stencils, BOM, PDFs, renders, fab README |

Run steps 1–3 after any schematic or library change, and steps 4–8 after any PCB-affecting change.
`finish` always rebuilds from a fresh placement, so it is safe to re-run.

**Acceptance gates before committing:** `NETLIST OK`; DRC **0 violations, 0 unconnected pads, 0
footprint errors**; `FIRMWARE OK` when firmware exists; then look at the renders.

## 4. Environment setup (cloud container, Ubuntu 24.04)

```sh
sudo apt-get update && sudo apt-get install -y --no-install-recommends kicad kicad-symbols kicad-footprints
pip install numpy scipy cairosvg     # router + renders (run with python3)
```

* Ubuntu 24.04 provides **KiCad 7.0.x**. The KiCad PPA is usually blocked by the network policy.
* `pcbnew` is importable only from the **system** interpreter: run PCB scripts with
  `/usr/bin/python3`, and router/render/check scripts with `python3`.
* KiCad 7 `kicad-cli` has **no DRC/ERC**. DRC runs through `pcbnew.WriteDRCReport()` in `gen_pcb.py`.
  The schematic is checked by `check_netlist.py` against `design.py`. Tell the user to run ERC once
  in the KiCad GUI.
* Running downloaded binaries or third-party code (e.g. the Freerouting jar, importing a downloaded
  library for a test) may be blocked by the sandbox's safety check. Don't work around it. The
  in-repo `router.py` replaces Freerouting. If you need to test third-party code, check it by
  inspection, and tell the user it was not executed.
* Many vendor sites (docs.arduino.cc, fab sites) are outside the network allowlist. Ask the user for
  the PDF or a screenshot rather than guessing. Network changes need the user's approval.

## 5. KiCad / generator gotchas (learned the hard way)

* **Bottom-side footprints:** `FOOTPRINT.Flip(pos, True)` mirrors X. A connector that must match
  a *top-view* pinout when mounted underneath (e.g. Nano headers) must be drawn **pre-mirrored** in
  its footprint. Assert pad positions after placement (`gen_pcb.py` checks pin 1 / pin 16 of J1).
* **Through-hole headers can short against a module on top** when rows overlap (Nano 15.24 mm vs
  Pico 17.78 mm). Use SMD headers on the bottom, or keep THT joints clear of the module.
* **Solder-jumper "Bridged" footprints are net ties** (`net_tie_pad_groups`). The router must treat
  their copper as belonging to both nets (`geometry.json` exports them as `shapes`).
* **Schematic labels:** put a wire stub on every pin and attach the label to the stub end. Never run
  a vertical wire past adjacent pin stubs (2.54 mm pitch): it silently shorts nets. Rotate GND
  symbols outward instead. `check_netlist.py` catches this.
* **KiCad 7 SWIG bug:** after removing tracks or zones from a loaded board, `board.Zones()` and
  `zone.Outline()` return untyped `SwigPyObject`s. Never edit a finished board. Rebuild from
  placement (`finish` calls `place()` first).
* **`pcbnew.ImportSpecctraSES` needs the GUI board.** `gen_pcb.py` parses `.ses` itself if you use
  Freerouting outside the sandbox.
* **Router (`router.py`):** a 0.2 mm grid A* on two layers with 45° moves and vias. Clearance comes from
  a distance transform of foreign copper, plus a `G/2` margin (`G` is the grid pitch). Board-edge
  distance uses a full `G` margin and a 1 mm grid border, because points on the edge count as inside.
  Required nets route first, then optional ones, then GND, which the pours complete. If routing fails,
  **change the pin mapping** so each group of signals keeps the same order on both connectors
  (fewer crossings). Spending more router passes rarely helps.
* **Pin-map strategy:** map the signals the target actually uses first, to hardware-capable pins
  (UART/I2C/SPI pin pairs, ADC). Wire spare pins only where they route cleanly. Check the full MCU
  function table, not just the pinout card (e.g. RP2040 UART1 on GP20/GP21 isn't on the Pico card).
* **Antenna / RF modules:** respect the datasheet keep-out. Cut a board notch rather than just
  leaving out copper, and keep copper out from under module test pads.
* **Silkscreen markings:** mark diode direction with a symbol plus net names, derived from the real
  pad positions (`diode_mark()`), and print capacitor values. Strokes ≥ 0.15 mm.

## 6. Manufacturing defaults

Design to the **strictest** fab the user might use, so one copper design fits all of them:

| Rule | Value used | Driven by |
|---|---|---|
| Track / space | ≥ 0.25 / 0.20 mm (signals), 0.5 mm power | margin over 6 mil |
| Via | 0.6 / 0.3 mm (power 0.8 / 0.4) | 0.3 mm min drill at JLCPCB / Seeed / 4project |
| Copper to edge | **0.4 mm** | OSH Park 15 mil |
| Silkscreen | strokes ≥ 0.15 mm | OSH Park ~5 mil, JLC 0.15 mm |
| Finish | ENIG recommended (flat pads for castellations / stencils) | |
| Passives | R / C **0603**; bulk capacitors (≥ 10 µF) **0805 or 1206**; nothing smaller than 0603 | hand assembly (root README "Design rules", checked by `check_bom.py`) |
| Custom parts | symbols / footprints in the shared `Libraries/` (KD_*), not project-local | reuse across designs |

`export_fab.sh` produces one board zip per fab, all from the same copper:

| Fab | Package |
|---|---|
| OSH Park | RS-274X, no X2, Protel names `.GTL/.GBL/.GTS/.GBS/.GTO/.GBO/.GKO`, drill `.XLN` (inch) |
| JLCPCB | KiCad default names (Protel extensions), Excellon mm, PTH/NPTH |
| Seeed Fusion | as OSH Park, drill `.TXT` |
| 4project.co.il | any of the above; default "6 mil / 0.3 mm" settings |
| Stencils | separate top / bottom zips: paste layer + outline. Apply module datasheet over-paste (e.g. Pico W +0.3 mm per side) via `solder_paste_margin` |

The user **hand-assembles**. Don't generate assembly-service files (CPL/LCSC BOM) unless asked. Do
write a hand-assembly order in the fab README (double-sided boards: which side first, alignment jigs,
polarity, pre-power checks).

## 7. Firmware

When a board replaces or adapts a controller, ship a port kit in `<Project>/firmware/`:
drop-in pin definition files, plus a patch script for the upstream library. The script must apply
every edit all-or-nothing, check the exact number of matches, and refuse to run twice. Add a
`check_firmware.py` that compares the pin map to `design.py`. Document platform limits (e.g. RP2040:
one extra thread).

## 8. Git workflow

* Work on the session's feature branch, and commit after each verified step with a descriptive message.
* Bump the board revision (`gen_schematic.py` title block, `gen_pcb.py` title block and silkscreen)
  for any change to copper or the electrical design, and regenerate outputs so file headers carry it.
* Push to `main` only when the user asks: fast-forward `main` to the feature branch.
* `build/`, `*.kicad_prl`, `*-backups/`, `__pycache__/` are ignored. Generated KiCad files and
  `fabrication/` **are** committed, so the repo is usable without running the tools.
* Never commit downloaded tools, wheels or other build debris.

## 9. Starting a new project – checklist

1. Collect datasheets, pinouts and schematics into `<NewProject>/Materials/`. Extract the key figures.
2. Copy `Pico_Alvik_Adapter/tools/` → `<NewProject>/tools/` and rename `PROJECT`/`LIB` in `design.py`.
3. Rewrite `design.py` with the pin tables, `SIGNALS` (required first), `build_nets()`, `COMPONENTS`,
   board geometry, keep-outs and the power design (state assumptions in comments).
4. Adapt `gen_libs.py` (custom symbols/footprints), `gen_schematic.py` (placement, notes) and
   `gen_pcb.py` (`BOTTOM_PARTS`, outline, keep-outs, silkscreen).
5. Run the pipeline (section 3) until all gates pass. Review the schematic PDF and the renders.
6. Write `<NewProject>/README.md` (overview, pin map, power design with sources, mechanical notes,
   regenerate steps) and `tools/fabrication_README.md` (fab table, stencils, hand assembly).
7. Add the project to the root `README.md` table. Commit and push the branch. Push `main` when
   asked.
