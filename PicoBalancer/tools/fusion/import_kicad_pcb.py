#!/usr/bin/env python3
"""Replace the Fusion placement-review blocks with the real KiCad board (stage 3).

    python import_kicad_pcb.py            # exports the STEP (kicad-cli), then imports it into Fusion (write access)
    python import_kicad_pcb.py --dry      # only writes the Fusion script

User request 2026-11-27: "update the pcb render in fusion360" (write permission for the review component).
What the Fusion script does:
* deletes the old "PCB_Review" (stage 0b blocks) and any earlier "PCB_KiCad*" occurrence;
* imports build/PicoBalancer.step (KiCad board, pads, silkscreen, all 3D models except the holders BT1 / BT2 -
  the Fusion holders stay) into a new component "PCB_KiCad" at the old PCB position;
* adds "PCB_KiCad_Extras": blocks for parts without a KiCad 3D model (Pico module + micro-USB, USB4235, slide switch).
Placement: STEP exported with origin at the board centre (x right, y up, board bottom z = 0).
Fusion: x_f = x, y_f = 121 + y_step, z_f = -5.5 + z (PCB bottom face at -5.5 mm, top at -3.9 mm).
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import design  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(os.path.dirname(HERE))
STEP = os.path.join(PRJ, "build", "PicoBalancer.step")
KICAD_CLI = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
EXTRA_REFS = ("U1 Pico W", "U1 micro-USB", "J5", "SW1", "SW1 actuator")
COLORS = {"pico": (0, 135, 75), "metal": (185, 185, 190), "conn": (235, 228, 210), "switch": (40, 40, 40),
          "white": (245, 245, 245)}


def export_step():
    refs = ",".join(r for r in design.PLACEMENT if not r.startswith("BT"))
    ox, oy = design.ORIGIN_X, design.ORIGIN_Y
    subprocess.run([KICAD_CLI, "pcb", "export", "step", "-o", STEP, "--user-origin", f"{ox}x{oy}mm",
                    "--component-filter", refs, "--include-pads", "--include-silkscreen", "--no-dnp",
                    "--subst-models", os.path.join(PRJ, f"{design.PROJECT}.kicad_pcb")], check=True)


data = {"step": STEP.replace("\\", "/"), "colors": COLORS,
        "extras": [list(p) for p in design.REVIEW_PARTS if p[0] in EXTRA_REFS]}

SCRIPT = r'''
import adsk.core, adsk.fusion, json
DATA = json.loads(@@DATA@@)
TOP = -0.39            # PCB top face, cm
def run(context):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    log = []
    for i in range(root.occurrences.count - 1, -1, -1):
        o = root.occurrences.item(i)
        if o.component.name.startswith('PCB_Review') or o.component.name.startswith('PCB_KiCad'):
            nm = o.name; o.deleteMe(); log.append('deleted ' + nm)
    # 1. KiCad board (STEP)
    m = adsk.core.Matrix3D.create()
    m.translation = adsk.core.Vector3D.create(0, 12.1, -0.55)
    occ = root.occurrences.addNewComponent(m)
    comp = occ.component
    comp.name = 'PCB_KiCad'
    im = app.importManager
    opts = im.createSTEPImportOptions(DATA['step'])
    opts.isViewFit = False
    ok = im.importToTarget(opts, comp)
    log.append('STEP import: %s, children %d' % (ok, comp.occurrences.count))
    bb = occ.boundingBox
    log.append('PCB_KiCad bbox mm x[%.2f, %.2f] y[%.2f, %.2f] z[%.2f, %.2f]' % (
        bb.minPoint.x*10, bb.maxPoint.x*10, bb.minPoint.y*10, bb.maxPoint.y*10, bb.minPoint.z*10, bb.maxPoint.z*10))
    # 2. blocks for parts without a KiCad model
    tbm = adsk.fusion.TemporaryBRepManager.get()
    eocc = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    ecomp = eocc.component
    ecomp.name = 'PCB_KiCad_Extras'
    lib = app.materialLibraries.itemByName('Fusion Appearance Library')
    src = None
    for nm in ('Plastic - Matte (Black)', 'Plastic - Glossy (Black)', 'Paint - Enamel Glossy (Black)'):
        try:
            src = lib.appearances.itemByName(nm)
        except Exception:
            src = None
        if src: break
    if src is None: src = lib.appearances.item(0)
    def appearance(kind):
        name = 'PBR_' + kind
        a = des.appearances.itemByName(name)
        if a is None:
            a = des.appearances.addByCopy(src, name)
            r, g, b = DATA['colors'][kind]
            for p in a.appearanceProperties:
                if p.objectType == adsk.core.ColorProperty.classType():
                    try:
                        p.value = adsk.core.Color.create(r, g, b, 0); break
                    except Exception:
                        pass
        return a
    parametric = des.designType == adsk.fusion.DesignTypes.ParametricDesignType
    bf = ecomp.features.baseFeatures.add() if parametric else None
    if bf: bf.startEdit()
    for ref, x, y, sx, sy, sz, kind, z0 in DATA['extras']:
        c = adsk.core.Point3D.create(x / 10.0, (121.0 - y) / 10.0, TOP + (z0 + sz / 2.0) / 10.0)
        obb = adsk.core.OrientedBoundingBox3D.create(c, adsk.core.Vector3D.create(1, 0, 0),
                                                     adsk.core.Vector3D.create(0, 1, 0), sx / 10.0, sy / 10.0, sz / 10.0)
        body = ecomp.bRepBodies.add(tbm.createBox(obb), bf) if bf else ecomp.bRepBodies.add(tbm.createBox(obb))
    if bf: bf.finishEdit()
    for i, (ref, x, y, sx, sy, sz, kind, z0) in enumerate(DATA['extras']):
        b = ecomp.bRepBodies.item(i)
        b.name = ref
        b.appearance = appearance(kind)
    log.append('extras: %d blocks' % ecomp.bRepBodies.count)
    old = root.bRepBodies.itemByName('PCB')
    if old and old.isLightBulbOn:
        old.isLightBulbOn = False; log.append('original PCB body hidden')
    print('\n'.join(log))
'''


def main():
    if "--dry" not in sys.argv and "--no-export" not in sys.argv:
        export_step()
    script = SCRIPT.replace("@@DATA@@", repr(json.dumps(data)))
    out = os.path.join(HERE, "fusion_import_script.py")
    open(out, "w", encoding="utf8").write(script)
    print(f"wrote {out}: STEP {STEP}, {len(data['extras'])} extra blocks")
    if "--dry" in sys.argv:
        return
    from fusion_mcp import run_script
    d = run_script(script, write=True)
    for c in d.get("result", {}).get("content", []):
        t = c.get("text", "")
        try:
            j = json.loads(t)
            print(j.get("message") or j.get("error") or t)
        except Exception:
            print(t)
    if "error" in d:
        print(d["error"])


if __name__ == "__main__":
    main()
