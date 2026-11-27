#!/usr/bin/env bash
# Export fabrication + documentation outputs with kicad-cli (KiCad 7+).
set -euo pipefail
cd "$(dirname "$0")/.."
# Portable tools: kicad-cli / python / zip from PATH, else the Windows defaults
KCLI="${KICAD_CLI:-$(command -v kicad-cli || echo "/c/Program Files/KiCad/10.0/bin/kicad-cli.exe")}"
kicad-cli() { "$KCLI" "$@"; }
PY="${PYTHON:-python3}"
"$PY" -c 'import numpy' 2>/dev/null || PY=python
command -v zip >/dev/null || zip() {    # zip -q out.zip files...
  shift; local out="$1"; shift
  "$PY" -c 'import sys, zipfile
with zipfile.ZipFile(sys.argv[1], "w", zipfile.ZIP_DEFLATED) as z:
    for f in sys.argv[2:]:
        z.write(f, f[2:] if f.startswith("./") else f)' "$out" "$@"; }
SVGMODE=""; [ "$(kicad-cli version | cut -d. -f1)" -ge 9 ] && SVGMODE="--mode-single"
P=Pico_Alvik_Adapter
F=fabrication
rm -rf "$F"; mkdir -p "$F/docs"

# ---------------------------------------------------------------------------
# PCB production: OSH Park style RS-274X gerbers (Protel extensions, plain
# RS-274X without X2 attributes, 4.6 mm coordinates) + one Excellon drill file
# ---------------------------------------------------------------------------
O="$F/production_oshpark"
T="$F/.tmp"
mkdir -p "$O" "$T"
kicad-cli pcb export gerbers \
    --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts" \
    --no-x2 --no-netlist --subtract-soldermask --precision 6 \
    -o "$T/" "$P.kicad_pcb" >/dev/null
kicad-cli pcb export drill --format excellon --excellon-units in \
    --excellon-zeros-format decimal --drill-origin absolute \
    -o "$T/" "$P.kicad_pcb" >/dev/null
mv "$T/$P-F_Cu.gtl"         "$O/$P.GTL"   # top copper
mv "$T/$P-B_Cu.gbl"         "$O/$P.GBL"   # bottom copper
mv "$T/$P-F_Mask.gts"       "$O/$P.GTS"   # top solder mask
mv "$T/$P-B_Mask.gbs"       "$O/$P.GBS"   # bottom solder mask
mv "$T/$P-F_Silkscreen.gto" "$O/$P.GTO"   # top silkscreen
mv "$T/$P-B_Silkscreen.gbo" "$O/$P.GBO"   # bottom silkscreen
mv "$T/$P-Edge_Cuts.gm1"    "$O/$P.GKO"   # board outline
mv "$T/$P.drl"              "$O/$P.XLN"   # drill (all holes plated)
rm -rf "$T"
rm -f "$O"/*.gbrjob
(cd "$O" && zip -q "../${P}_OSHPark.zip" ./*)

# Seeed Fusion: same RS-274X set, Protel names, Excellon drill as .TXT
SD="$F/production_seeed"; mkdir -p "$SD"
cp "$O"/$P.G* "$SD/"
cp "$O/$P.XLN" "$SD/$P.TXT"
(cd "$SD" && zip -q "../${P}_Seeed.zip" ./*)

# JLCPCB: KiCad default gerber names (Protel extensions) + PTH/NPTH Excellon (mm)
# (PCB only - the board is hand-assembled)
J="$F/production_jlcpcb"; mkdir -p "$J"
kicad-cli pcb export gerbers \
    --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts" \
    --subtract-soldermask --precision 6 -o "$J/" "$P.kicad_pcb" >/dev/null
kicad-cli pcb export drill --format excellon --excellon-units mm \
    --excellon-separate-th -o "$J/" "$P.kicad_pcb" >/dev/null
rm -f "$J"/*.gbrjob
(cd "$J" && zip -q "../${P}_JLCPCB.zip" ./*)

# ---------------------------------------------------------------------------
# SMT stencils: paste layer + board outline (for alignment), one set per side
# ---------------------------------------------------------------------------
for side in top bottom; do
  if [ $side = top ]; then L=F.Paste; X=gtp; N=GTP; else L=B.Paste; X=gbp; N=GBP; fi
  D="$F/stencil_$side"; mkdir -p "$D"
  kicad-cli pcb export gerbers --layers "$L,Edge.Cuts" --no-x2 --no-netlist \
      --precision 6 -o "$D/" "$P.kicad_pcb" >/dev/null
  mv "$D/$P-${L/./_}.$X" "$D/${P}_stencil_$side.$N"
  mv "$D/$P-Edge_Cuts.gm1" "$D/${P}_outline.GKO"
  rm -f "$D"/*.gbrjob
  (cd "$D" && zip -q "../${P}_stencil_$side.zip" ./*)
done

kicad-cli pcb export pos --side both --format csv --units mm \
    -o "$F/${P}_positions.csv" "$P.kicad_pcb"
kicad-cli sch export python-bom -o "$F/docs/${P}_bom.xml" "$P.kicad_sch" >/dev/null
"$PY" tools/make_bom.py "$F/docs/${P}_bom.xml" "$F/${P}_BOM.csv"
rm -f "$F/docs/${P}_bom.xml"

kicad-cli sch export pdf -o "$F/docs/${P}_schematic.pdf" "$P.kicad_sch"
kicad-cli pcb export pdf --layers "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts" \
    -o "$F/docs/${P}_pcb_top.pdf" "$P.kicad_pcb"
kicad-cli pcb export pdf --layers "B.Cu,B.Silkscreen,B.Mask,Edge.Cuts" --mirror \
    -o "$F/docs/${P}_pcb_bottom.pdf" "$P.kicad_pcb"

# PNG previews (SVG -> PNG)
for side in top bottom; do
  if [ $side = top ]; then L="F.Cu,F.Silkscreen,F.Mask,Edge.Cuts,F.Fab"; M=""; else L="B.Cu,B.Silkscreen,B.Mask,Edge.Cuts,B.Fab"; M="--mirror"; fi
  kicad-cli pcb export svg --layers "$L" $M --exclude-drawing-sheet --page-size-mode 2 $SVGMODE \
      -o "$F/docs/${P}_$side.svg" "$P.kicad_pcb" >/dev/null
  "$PY" -c "import sys; sys.path.insert(0, 'tools'); from render_board import svg_to_png; open(sys.argv[2], 'wb').write(svg_to_png(sys.argv[1], 900))" \
      "$F/docs/${P}_$side.svg" "$F/docs/${P}_$side.png"
done
"$PY" tools/render_board.py >/dev/null
cp tools/fabrication_README.md "$F/README.md"
echo "outputs in $F/"
