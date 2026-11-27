
import adsk.core, adsk.fusion, json
DATA = json.loads('{"step": "C:/WorkSpace_Projects/KiCad-Designs/PicoBalancer/build/PicoBalancer.step", "colors": {"pico": [0, 135, 75], "metal": [185, 185, 190], "conn": [235, 228, 210], "switch": [40, 40, 40], "white": [245, 245, 245]}, "extras": [["J5", 0.0, -93.0, 8.94, 3.16, 6.5, "conn", 0], ["U1 Pico W", 0.0, 52.5, 21.0, 51.0, 1.0, "pico", 8.5], ["U1 micro-USB", 0.0, 28.3, 7.5, 5.5, 2.7, "metal", 9.5], ["SW1", 20.25, 28.3, 5.4, 9.8, 9.1, "switch", 0], ["SW1 actuator", 20.25, 28.3, 2.4, 2.4, 2.5, "white", 9.1]]}')
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
