#!/usr/bin/env python3
"""Build the placement-review component in the Fusion 360 model from design.py (stage 0b).

    python build_review.py            # writes fusion_review_script.py and runs it in Fusion (write access)
    python build_review.py --dry      # only writes the script

What the Fusion script does (user permission 2026-11-27 to edit the Fusion project):
* deletes an earlier "PCB_Review" occurrence (so the build can be rerun) and creates a new one at the origin;
* PCB_review body: 60 x 200 x 1.6 mm board at the old PCB position, 6 bolt holes + 4 holder locating holes;
* one coloured block per part in design.REVIEW_PARTS, standing on the board top (Fusion z = -3.9 mm);
* hides the original root body "PCB" (not deleted);
* moves the two 18650 holder occurrences to design.BT_POS (housing flush with the board's long edges).
Coordinates: Fusion x = x, y = 121 - y, z = -3.9 + z (mm); Fusion API works in cm.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import design  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

COLORS = {"pcb": (25, 85, 45), "ic": (45, 45, 48), "conn": (235, 228, 210), "ind": (120, 120, 125),
          "cap": (205, 170, 110), "prot": (230, 130, 30), "socket": (25, 25, 25), "pico": (0, 135, 75),
          "metal": (185, 185, 190), "switch": (40, 40, 40), "white": (245, 245, 245),
          "led_red": (220, 40, 40), "led_green": (40, 190, 70), "keepout": (230, 60, 60), "res": (30, 30, 30), "led_blue": (40, 90, 230)}

data = {
    "board": [design.BOARD_W, design.BOARD_H, design.BOARD_T],
    "holes": [[x, y, design.HOLE_D] for x, y in design.HOLES] + [list(h) for h in design.HOLDER_HOLES]
             + [list(h) for h in design.CLAMP_HOLES],
    "parts": [list(p) for p in design.REVIEW_PARTS],
    "colors": COLORS,
    "keepout": [[x, y, 2 * design.BOLT_KEEPOUT_R] for x, y in design.HOLES],
    "holders": {"left": [-design.BOARD_W / 2, -design.BOARD_W / 2 + design.HOLDER["body"][0]],
                "right": [design.BOARD_W / 2 - design.HOLDER["body"][0], design.BOARD_W / 2],
                "y_top": design.BT_POS["BT1"][1] - design.HOLDER["body"][1] / 2},   # board y of the housing's top end
}

SCRIPT = r'''
import adsk.core, adsk.fusion, json
DATA = json.loads(%r)
TOP = -0.39            # PCB top face, cm
def P(x, y, z): return adsk.core.Point3D.create(x / 10.0, (121.0 - y) / 10.0, z / 10.0)

def run(context):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    tbm = adsk.fusion.TemporaryBRepManager.get()
    log = []
    # 1. remove an earlier review component
    for i in range(root.occurrences.count - 1, -1, -1):
        o = root.occurrences.item(i)
        if o.component.name.startswith('PCB_Review'):
            nm = o.name; o.deleteMe(); log.append('deleted old ' + nm)
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = 'PCB_Review'
    # appearances
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
    def box(cx, cy, z0, sx, sy, sz):
        c = P(cx, cy, 0)
        c = adsk.core.Point3D.create(c.x, c.y, TOP + (z0 + sz / 2.0) / 10.0)
        obb = adsk.core.OrientedBoundingBox3D.create(c, adsk.core.Vector3D.create(1, 0, 0),
                                                     adsk.core.Vector3D.create(0, 1, 0), sx / 10.0, sy / 10.0, sz / 10.0)
        return tbm.createBox(obb)
    # 2. board with holes
    W, H, T = DATA['board']
    board = box(0, 0, -T, W, H, T)
    for x, y, d in DATA['holes']:
        a = P(x, y, 0); a = adsk.core.Point3D.create(a.x, a.y, TOP - T / 10.0 - 0.1)
        b = adsk.core.Point3D.create(a.x, a.y, TOP + 0.1)
        tbm.booleanOperation(board, tbm.createCylinderOrCone(a, d / 20.0, b, d / 20.0),
                             adsk.fusion.BooleanTypes.DifferenceBooleanType)
    items = [('PCB_review', board, 'pcb')]
    for x, y, d in DATA['keepout']:                 # M2.5 head keep-out marker: 7.5 mm disc, 0.05 mm on the board top
        a = P(x, y, 0); a = adsk.core.Point3D.create(a.x, a.y, TOP)
        b = adsk.core.Point3D.create(a.x, a.y, TOP + 0.005)
        disc = tbm.createCylinderOrCone(a, d / 20.0, b, d / 20.0)
        tbm.booleanOperation(disc, tbm.createCylinderOrCone(a, 0.1325, b, 0.1325), adsk.fusion.BooleanTypes.DifferenceBooleanType)
        items.append(('Keep-out 7.5mm (%.0f, %.0f)' % (x, y), disc, 'keepout'))
    for ref, x, y, sx, sy, sz, kind, z0 in DATA['parts']:
        items.append((ref, box(x, y, z0, sx, sy, sz), kind))
    parametric = des.designType == adsk.fusion.DesignTypes.ParametricDesignType
    bf = comp.features.baseFeatures.add() if parametric else None
    if bf: bf.startEdit()
    made = []
    for name, body, kind in items:
        nb = comp.bRepBodies.add(body, bf) if bf else comp.bRepBodies.add(body)
        made.append((nb, name, kind))
    if bf: bf.finishEdit()
    for i, (name, body, kind) in enumerate(items):
        b = comp.bRepBodies.item(i)
        b.name = name
        b.appearance = appearance(kind)
    log.append('review bodies: %%d' %% comp.bRepBodies.count)
    # 3. hide the original PCB body
    old = root.bRepBodies.itemByName('PCB')
    if old:
        old.isLightBulbOn = False; log.append('original PCB body hidden')
    # 4. move the holders: housing (Base body) flush with the board edges, top end at y_top.
    #    A holder held by a rigid joint to the old PCB (left holder: Rigid 6, frame X = world -x, Y = world -y)
    #    is moved by editing that joint's offsets; a free holder by its transform + a captured position.
    hd = DATA['holders']
    for o in root.occurrences:
        if '18650' not in o.name or 'Battery 01A' in o.name: continue
        base = None
        for c in o.childOccurrences:
            if 'Base' in c.name and c.bRepBodies.count: base = c.bRepBodies.item(0)
        if base is None: continue
        bb = base.boundingBox
        cx = (bb.minPoint.x + bb.maxPoint.x) / 2.0
        tx0, tx1 = hd['left'] if cx < 0 else hd['right']
        dx = tx0 / 10.0 - bb.minPoint.x
        dy = (121.0 - hd['y_top']) / 10.0 - bb.maxPoint.y
        joint = None
        kids = [c.name for c in o.childOccurrences]
        for jt in root.joints:
            try:
                if not jt.isSuppressed and jt.occurrenceTwo is None and jt.occurrenceOne and jt.occurrenceOne.name in kids:
                    joint = jt
            except Exception:
                pass
        if joint is not None:
            joint.offsetX.value = joint.offsetX.value - dx
            joint.offsetY.value = joint.offsetY.value - dy
            log.append('%s moved via %s offsets (dx %.3f, dy %.3f mm): X=%s Y=%s' % (o.name, joint.name, dx*10, dy*10, joint.offsetX.expression, joint.offsetY.expression))
        else:
            m = o.transform2; t = m.translation; t.add(adsk.core.Vector3D.create(dx, dy, 0)); m.translation = t; o.transform2 = m
            if parametric and des.snapshots.hasPendingSnapshot: des.snapshots.add()
            log.append('%s moved via transform (dx %.3f, dy %.3f mm)' % (o.name, dx*10, dy*10))
    try:
        if parametric and des.snapshots.hasPendingSnapshot: des.snapshots.add()
    except Exception as e:
        log.append('snapshot: ' + str(e))
    for o in root.occurrences:
        if '18650' not in o.name or 'Battery 01A' in o.name: continue
        for c in o.childOccurrences:
            if 'Base' in c.name and c.bRepBodies.count:
                bb = c.bRepBodies.item(0).boundingBox
                log.append('%%s housing x[%%.2f, %%.2f] y_f[%%.2f, %%.2f]' %% (o.name, bb.minPoint.x*10, bb.maxPoint.x*10, bb.minPoint.y*10, bb.maxPoint.y*10))
    print('\n'.join(log))
'''


def main():
    # the template mixes escaped (%%) and plain (%) format strings: substitute the data placeholder by hand
    script = SCRIPT.replace("%r", "@@DATA@@", 1).replace("%%", "%").replace("@@DATA@@", repr(json.dumps(data)))
    out = os.path.join(HERE, "fusion_review_script.py")
    open(out, "w", encoding="utf8").write(script)
    print(f"wrote {out}: {len(data['parts'])} parts, {len(data['holes'])} holes")
    if "--dry" not in sys.argv:
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
