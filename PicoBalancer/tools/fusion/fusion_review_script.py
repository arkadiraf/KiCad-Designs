
import adsk.core, adsk.fusion, json
DATA = json.loads('{"board": [60.0, 200.0, 1.6], "holes": [[-26.0, -96.0, 2.65], [26.0, -96.0, 2.65], [-26.0, 0.0, 2.65], [26.0, 0.0, 2.65], [-26.0, 96.0, 2.65], [26.0, 96.0, 2.65], [-11.675, -22.375, 2.39], [-27.675, -77.575, 3.45], [27.675, -22.375, 2.39], [11.675, -77.575, 3.45], [0.0, -61.0, 2.65], [0.0, -81.0, 2.65]], "parts": [["J5", 0.0, -91.0, 8.94, 3.16, 6.5, "conn", 0], ["C20", -7.0, -91.0, 1.6, 0.8, 0.8, "cap", 0], ["U6", 0.0, -48.0, 4.0, 4.0, 0.9, "ic", 0], ["L1", 0.0, -40.0, 4.1, 4.1, 3.1, "ind", 0], ["C21", -6.0, -50.0, 2.0, 1.25, 1.25, "cap", 0], ["C22", -6.0, -46.0, 2.0, 1.25, 1.25, "cap", 0], ["C23", 6.0, -50.0, 2.0, 1.25, 1.25, "cap", 0], ["C24", 6.0, -46.0, 2.0, 1.25, 1.25, "cap", 0], ["C25", 6.0, -40.0, 2.0, 1.25, 1.25, "cap", 0], ["D1", -6.0, -36.0, 2.0, 1.25, 0.8, "led_red", 0], ["F1", -12.0, -5.0, 4.5, 3.2, 0.9, "prot", 0], ["Q1", -12.0, 2.0, 3.3, 3.3, 0.8, "ic", 0], ["Q3", -6.5, 2.0, 2.9, 1.3, 1.1, "ic", 0], ["F2", 12.0, -5.0, 4.5, 3.2, 0.9, "prot", 0], ["Q2", 12.0, 2.0, 3.3, 3.3, 0.8, "ic", 0], ["Q4", 6.5, 2.0, 2.9, 1.3, 1.1, "ic", 0], ["J1", -8.89, 39.5, 2.54, 50.8, 8.5, "socket", 0], ["J2", 8.89, 39.5, 2.54, 50.8, 8.5, "socket", 0], ["U1 Pico W", 0.0, 39.5, 21.0, 51.0, 1.0, "pico", 8.5], ["U1 micro-USB", 0.0, 15.3, 7.5, 5.5, 2.7, "metal", 9.5], ["U2 BNO086", 0.0, 89.0, 3.8, 5.2, 1.1, "ic", 0], ["Y1", 5.0, 89.0, 3.2, 1.5, 0.9, "metal", 0], ["U3", -14.0, 85.0, 2.0, 2.0, 0.8, "ic", 0], ["C6", -18.0, 85.0, 2.0, 1.25, 1.25, "cap", 0], ["J3", -14.0, 96.5, 8.0, 4.25, 2.95, "conn", 0], ["U4", 14.0, 85.0, 2.0, 2.0, 0.8, "ic", 0], ["C7", 18.0, 85.0, 2.0, 1.25, 1.25, "cap", 0], ["J4", 14.0, 96.5, 8.0, 4.25, 2.95, "conn", 0], ["U5", -20.0, 62.0, 2.5, 2.5, 1.0, "ic", 0], ["L2", -20.0, 70.0, 4.1, 4.1, 3.1, "ind", 0], ["C16", -26.5, 56.0, 3.2, 1.6, 1.6, "cap", 0], ["C17", -26.5, 60.0, 3.2, 1.6, 1.6, "cap", 0], ["C18", -26.5, 64.0, 3.2, 1.6, 1.6, "cap", 0], ["C14", -14.5, 58.0, 2.0, 1.25, 1.25, "cap", 0], ["C15", -14.5, 62.0, 2.0, 1.25, 1.25, "cap", 0], ["U7", 18.0, 32.0, 2.9, 2.8, 1.1, "ic", 0], ["D2", 18.0, 40.0, 3.7, 1.6, 1.1, "ic", 0], ["SW1", 27.4, 36.0, 4.0, 11.6, 5.4, "switch", 0], ["SW1 actuator", 27.4, 36.0, 2.0, 2.0, 2.0, "white", 5.4], ["D3", 20.0, 46.0, 2.0, 1.25, 0.8, "led_green", 0]], "colors": {"pcb": [25, 85, 45], "ic": [45, 45, 48], "conn": [235, 228, 210], "ind": [120, 120, 125], "cap": [205, 170, 110], "prot": [230, 130, 30], "socket": [25, 25, 25], "pico": [0, 135, 75], "metal": [185, 185, 190], "switch": [40, 40, 40], "white": [245, 245, 245], "led_red": [220, 40, 40], "led_green": [40, 190, 70], "keepout": [230, 60, 60]}, "keepout": [[-26.0, -96.0, 15.0], [26.0, -96.0, 15.0], [-26.0, 0.0, 15.0], [26.0, 0.0, 15.0], [-26.0, 96.0, 15.0], [26.0, 96.0, 15.0]], "holders": {"left": [-30.0, -9.350000000000001], "right": [9.350000000000001, 30.0], "y_top": -88.5}}')
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
    for x, y, d in DATA['keepout']:                 # M2.5 head keep-out marker: 15 mm disc, 0.05 mm on the board top
        a = P(x, y, 0); a = adsk.core.Point3D.create(a.x, a.y, TOP)
        b = adsk.core.Point3D.create(a.x, a.y, TOP + 0.005)
        disc = tbm.createCylinderOrCone(a, d / 20.0, b, d / 20.0)
        tbm.booleanOperation(disc, tbm.createCylinderOrCone(a, 0.1325, b, 0.1325), adsk.fusion.BooleanTypes.DifferenceBooleanType)
        items.append(('Keep-out 15mm (%.0f, %.0f)' % (x, y), disc, 'keepout'))
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
    log.append('review bodies: %d' % comp.bRepBodies.count)
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
                log.append('%s housing x[%.2f, %.2f] y_f[%.2f, %.2f]' % (o.name, bb.minPoint.x*10, bb.maxPoint.x*10, bb.minPoint.y*10, bb.maxPoint.y*10))
    print('\n'.join(log))
