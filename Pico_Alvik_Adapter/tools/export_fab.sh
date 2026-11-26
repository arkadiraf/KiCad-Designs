#!/usr/bin/env bash
# Export fabrication + documentation outputs with kicad-cli (KiCad 7+).
set -euo pipefail
cd "$(dirname "$0")/.."
P=Pico_Alvik_Adapter
F=fabrication
rm -rf "$F"; mkdir -p "$F/gerbers" "$F/docs"

LAYERS="F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
kicad-cli pcb export gerbers --layers "$LAYERS" --subtract-soldermask \
    -o "$F/gerbers/" "$P.kicad_pcb"
kicad-cli pcb export drill --format excellon --excellon-separate-th \
    --generate-map --map-format gerberx2 -o "$F/gerbers/" "$P.kicad_pcb"
(cd "$F/gerbers" && zip -q "../${P}_gerbers.zip" ./*)

kicad-cli pcb export pos --side both --format csv --units mm \
    -o "$F/${P}_positions.csv" "$P.kicad_pcb"
kicad-cli sch export python-bom -o "$F/docs/${P}_bom.xml" "$P.kicad_sch" >/dev/null
python3 tools/make_bom.py "$F/docs/${P}_bom.xml" "$F/${P}_BOM.csv"
rm -f "$F/docs/${P}_bom.xml"

kicad-cli sch export pdf -o "$F/docs/${P}_schematic.pdf" "$P.kicad_sch"
kicad-cli pcb export pdf --layers "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts" \
    -o "$F/docs/${P}_pcb_top.pdf" "$P.kicad_pcb"
kicad-cli pcb export pdf --layers "B.Cu,B.Silkscreen,B.Mask,Edge.Cuts" --mirror \
    -o "$F/docs/${P}_pcb_bottom.pdf" "$P.kicad_pcb"

# PNG previews (SVG -> PNG)
for side in top bottom; do
  if [ $side = top ]; then L="F.Cu,F.Silkscreen,F.Mask,Edge.Cuts,F.Fab"; M=""; else L="B.Cu,B.Silkscreen,B.Mask,Edge.Cuts,B.Fab"; M="--mirror"; fi
  kicad-cli pcb export svg --layers "$L" $M --exclude-drawing-sheet --page-size-mode 2 \
      -o "$F/docs/${P}_$side.svg" "$P.kicad_pcb" >/dev/null
  python3 -c "import cairosvg,sys; cairosvg.svg2png(url=sys.argv[1], write_to=sys.argv[2], output_width=900, background_color='white')" \
      "$F/docs/${P}_$side.svg" "$F/docs/${P}_$side.png"
done
python3 tools/render_board.py >/dev/null
echo "outputs in $F/"
