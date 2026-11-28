#!/usr/bin/env bash
# PicoBalancer fabrication outputs (kicad-cli, KiCad 10). Run from anywhere: bash tools/export_fab.sh
#
# OSH Park 2-layer (docs.oshpark.com, checked 2026-11-28):
#   * .kicad_pcb upload is processed with KiCad 9.x - this board is KiCad 10 format, so upload the Gerber zip.
#   * RS-274X, Protel names (.GTL .GBL .GTS .GBS .GTO .GBO .GKO), Excellon drill .XLN:
#     inches, decimal zeros, absolute origin, slots as G85 ("alternate drill mode"), one merged file.
#   * Zones are not re-filled by the fab: the board is filled by gen_pcb.py finish.
# Stencil (top only - all parts are on top): F.Paste + outline, e.g. for OSH Stencils.
# The BOM files in fabrication/ are produced by export_bom.py and are left untouched here.
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
P=PicoBalancer
F=fabrication
O="$F/production_oshpark"; S="$F/stencil_top"; D="$F/docs"; T="build/fab_tmp"
rm -rf "$O" "$S" "$T" "$F/${P}_OSHPark.zip" "$F/${P}_stencil_top.zip"
mkdir -p "$O" "$S" "$D" "$T"

# --- PCB: Gerbers + drill -----------------------------------------------------
kicad-cli pcb export gerbers \
    --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts" \
    --no-x2 --no-netlist --subtract-soldermask --precision 6 \
    -o "$T/" "$P.kicad_pcb" >/dev/null
kicad-cli pcb export drill --format excellon --excellon-units in \
    --excellon-zeros-format decimal --drill-origin absolute --excellon-oval-format alternate \
    -o "$T/" "$P.kicad_pcb" >/dev/null
mv "$T/$P-F_Cu.gtl"         "$O/$P.GTL"   # top copper
mv "$T/$P-B_Cu.gbl"         "$O/$P.GBL"   # bottom copper
mv "$T/$P-F_Mask.gts"       "$O/$P.GTS"   # top solder mask
mv "$T/$P-B_Mask.gbs"       "$O/$P.GBS"   # bottom solder mask
mv "$T/$P-F_Silkscreen.gto" "$O/$P.GTO"   # top silkscreen
mv "$T/$P-B_Silkscreen.gbo" "$O/$P.GBO"   # bottom silkscreen (empty)
mv "$T/$P-Edge_Cuts.gm1"    "$O/$P.GKO"   # board outline
mv "$T/$P.drl"              "$O/$P.XLN"   # drill: PTH + NPTH + J5 plated slots (G85)
zipdir "$F/${P}_OSHPark.zip" "$O"

# --- Top stencil ----------------------------------------------------------------
kicad-cli pcb export gerbers --layers "F.Paste,Edge.Cuts" --no-x2 --no-netlist --precision 6 \
    -o "$T/" "$P.kicad_pcb" >/dev/null
mv "$T/$P-F_Paste.gtp"   "$S/${P}_stencil_top.GTP"
mv "$T/$P-Edge_Cuts.gm1" "$S/${P}_outline.GKO"
zipdir "$F/${P}_stencil_top.zip" "$S"

# --- Assembly aids --------------------------------------------------------------
kicad-cli pcb export pos --side front --format csv --units mm --exclude-dnp \
    -o "$F/${P}_positions.csv" "$P.kicad_pcb" >/dev/null
kicad-cli pcb export pdf --layers "F.Fab,F.Silkscreen,Edge.Cuts" --exclude-value \
    -o "$D/${P}_assembly_top.pdf" "$P.kicad_pcb" >/dev/null 2>&1 || \
kicad-cli pcb export pdf --layers "F.Fab,F.Silkscreen,Edge.Cuts" -o "$D/${P}_assembly_top.pdf" "$P.kicad_pcb" >/dev/null
kicad-cli pcb export pdf --layers "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts" -o "$D/${P}_pcb_top.pdf" "$P.kicad_pcb" >/dev/null
kicad-cli pcb export pdf --layers "B.Cu,B.Silkscreen,B.Mask,Edge.Cuts" --mirror -o "$D/${P}_pcb_bottom.pdf" "$P.kicad_pcb" >/dev/null
rm -rf "$T"
ls -la "$F"/*.zip "$O" "$S"
