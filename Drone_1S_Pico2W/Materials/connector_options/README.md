# Board-to-board connector options (FC <-> frame), Nov 2026

The candidates looked at for J1/J2 (FC top, male) and J5/J6 (frame bottom, female). The parts that were
chosen have their datasheets in `../bom_datasheets/`. This folder keeps the other options for reference
(this content used to be in `todo/`).

**Chosen (28 Nov 2026), 2.00 mm, on 7 mm M2 standoffs:**

| Ref | Part | Digi-Key | Key dimensions (from the drawing) |
|---|---|---|---|
| FC J1 J2 | Würth WR-PHD 62001011121, THT male 1x10 | 732-62001011121-ND | plastic 2.0, pin 4.0 above it, tail 2.7, 0.5 sq, hole 0.9, 2 A |
| Frame J5 J6 | Sullins NPPN101BFLD-RC, SMD female 1x10 | S5902-10-ND | body 4.40 (4.60 +-0.25 overall), contact point 2.50 below the top, pads 0.90 x 2.0 staggered, 5.20 outer span, 2 A; nylon 6T = hand / wave soldering only |

Mated: 2.0 + 4.6 = 6.6 mm fully seated. On 7 mm standoffs the pin goes about 3.6 mm in (1.1 mm past the
contact point) with about 0.4 mm of air between the plastics. 6 or 6.5 mm standoffs can make the plastics
collide at the tolerance limits.

**Not chosen:**

| File | Part | Why not |
|---|---|---|
| `Harwin_Archer_M50_1.27mm_brochure.pdf` | Harwin M50-3531042 / M50-3631042R / M50-3141045R, 1.27 mm | 1.27 mm pitch: needs new footprints and a pitch change; the brochure has no dimension drawings |
| `62001011821_Wurth_datasheet.pdf` | Würth WR-PHD THT socket, 4.3 mm | through-hole: the 2.7 mm tails come out on the frame top under the battery-cover rails |
| `SMM-1xx_Samtec_socket_drawing.pdf` | Samtec SMM-110-02-S-S, 3.68 mm SMD | works on 6 mm with TMM-110-02, but dearer; the Sullins + Würth pair is stocked locally |
| `NRPN101PAEN-RC_Sullins_male_drawing_10531.pdf` | Sullins 2 mm THT male | plastic 2.0, pins 3.6 / 2.8 mm: also usable; the Würth part was picked |
| Samtec TMM-110-01-L-S | 3.2 mm post | too short for the 4.6 mm Sullins socket (2.3 mm in, short of the 2.5 mm contact point) |

`*.png` are the Digi-Key search screenshots; `todo_digikey_candidates.txt` is the original candidate list.
SWD on J9 uses the Raspberry Pi Debug Probe's own JST-SH 3-pin cable (no separate jumper ordered).

The Flow deck headers P1/P2 (2.00 mm, fixed by the Bitcraze sockets): Samtec **TMM-110-01-T-S-SM-P-TR** (tin, cut tape 612-TMM-110-01-T-S-SM-P-CT-ND; the gold -G-S-SM is out of stock), same SM footprint as the hard-to-get -04. Its 3.20 mm posts must be **trimmed to about 1.9 mm** with flush cutters after soldering, so the Flow deck's 2.1 mm sockets seat against the plastic.
