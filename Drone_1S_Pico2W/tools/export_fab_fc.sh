#!/usr/bin/env bash
# FC module fabrication outputs (kicad-cli, KiCad 10). Run from anywhere: bash tools/export_fab_fc.sh
# Template: PicoBalancer/tools/export_fab.sh.
#
# OSH Park 2-layer (docs.oshpark.com): prototype at 1.6 mm (later 0.8 mm "2 layer thin" - same Gerbers).
#   * The .kicad_pcb upload is processed with KiCad 9.x - this board is KiCad 10 format, so upload the Gerber zip.
#   * RS-274X, Protel names (.GTL .GBL .GTS .GBS .GTO .GBO .GKO), Excellon drill .XLN: inches, decimal,
#     absolute origin, one merged file (PTH + NPTH).
#   * Pours are filled by gen_pcb.py fc finish (kicad-cli --refill-zones); the fab does not refill.
# Stencils: parts on BOTH sides (Pico 2 W + J1/J2 on top; sensors, passives, P1/P2, J9, SW1 on the bottom),
# so a top and a bottom paste layer, each with the outline (e.g. OSH Stencils).
set -euo pipefail
cd "$(dirname "$0")/.."
KCLI="${KICAD_CLI:-$(command -v kicad-cli || echo "/c/Program Files/KiCad/10.0/bin/kicad-cli.exe")}"
kicad-cli() { "$KCLI" "$@"; }
PY="${PYTHON:-/c/Program Files/KiCad/10.0/bin/python.exe}"
zipdir() {   # zipdir out.zip dir  (flat zip of the files in dir)
  "$PY" -I -c 'import sys, os, zipfile
out, d = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(d)): z.write(os.path.join(d, f), f)' "$1" "$2"; }
P=Drone_1S_FC
B=FC/$P.kicad_pcb
F=fabrication/fc
O="$F/production_oshpark"; ST="$F/stencil_top"; SB="$F/stencil_bottom"; D="$F/docs"; T="build/fab_fc_tmp"
rm -rf "$O" "$ST" "$SB" "$T" "$F/${P}_OSHPark.zip" "$F/${P}_stencil_top.zip" "$F/${P}_stencil_bottom.zip"
mkdir -p "$O" "$ST" "$SB" "$D" "$T"

# --- PCB: Gerbers + drill -----------------------------------------------------
kicad-cli pcb export gerbers \
    --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts" \
    --no-x2 --no-netlist --subtract-soldermask --precision 6 \
    -o "$T/" "$B" >/dev/null
kicad-cli pcb export drill --format excellon --excellon-units in \
    --excellon-zeros-format decimal --drill-origin absolute --excellon-oval-format alternate \
    -o "$T/" "$B" >/dev/null
mv "$T/$P-F_Cu.gtl"         "$O/$P.GTL"   # top copper
mv "$T/$P-B_Cu.gbl"         "$O/$P.GBL"   # bottom copper
mv "$T/$P-F_Mask.gts"       "$O/$P.GTS"   # top solder mask
mv "$T/$P-B_Mask.gbs"       "$O/$P.GBS"   # bottom solder mask
mv "$T/$P-F_Silkscreen.gto" "$O/$P.GTO"   # top silkscreen
mv "$T/$P-B_Silkscreen.gbo" "$O/$P.GBO"   # bottom silkscreen
mv "$T/$P-Edge_Cuts.gm1"    "$O/$P.GKO"   # board outline
mv "$T/$P.drl"              "$O/$P.XLN"   # drill: PTH + NPTH
zipdir "$F/${P}_OSHPark.zip" "$O"

# --- Stencils -------------------------------------------------------------------
kicad-cli pcb export gerbers --layers "F.Paste,B.Paste,Edge.Cuts" --no-x2 --no-netlist --precision 6 \
    -o "$T/" "$B" >/dev/null
cp "$T/$P-Edge_Cuts.gm1" "$ST/${P}_outline.GKO"
mv "$T/$P-Edge_Cuts.gm1" "$SB/${P}_outline.GKO"
mv "$T/$P-F_Paste.gtp"   "$ST/${P}_stencil_top.GTP"
mv "$T/$P-B_Paste.gbp"   "$SB/${P}_stencil_bottom.GBP"
zipdir "$F/${P}_stencil_top.zip" "$ST"
zipdir "$F/${P}_stencil_bottom.zip" "$SB"

# --- Assembly aids --------------------------------------------------------------
kicad-cli pcb export pos --side both --format csv --units mm --exclude-dnp \
    -o "$F/${P}_positions.csv" "$B" >/dev/null
kicad-cli pcb export pdf --layers "F.Fab,F.Silkscreen,Edge.Cuts" -o "$D/${P}_assembly_top.pdf" "$B" >/dev/null 2>&1 || true
kicad-cli pcb export pdf --layers "B.Fab,B.Silkscreen,Edge.Cuts" --mirror -o "$D/${P}_assembly_bottom.pdf" "$B" >/dev/null 2>&1 || true
kicad-cli pcb export pdf --layers "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts" -o "$D/${P}_pcb_top.pdf" "$B" >/dev/null
kicad-cli pcb export pdf --layers "B.Cu,B.Silkscreen,B.Mask,Edge.Cuts" --mirror -o "$D/${P}_pcb_bottom.pdf" "$B" >/dev/null
kicad-cli sch export pdf -o "$D/${P}_schematic.pdf" "FC/$P.kicad_sch" >/dev/null
rm -rf "$T"
ls -la "$F"/*.zip "$O" "$ST" "$SB"
