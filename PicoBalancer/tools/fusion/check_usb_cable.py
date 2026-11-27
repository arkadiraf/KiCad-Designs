import adsk.core, adsk.fusion
# USB-C cable envelope over J5 (vertical receptacle at board (0, -93) -> Fusion (0, 214)): USB-IF max overmold
# 12.35 x 6.5 mm from 6.5 mm above the PCB (GCT mating view) to 26.5 mm, then a 4.5 mm cable up to 60 mm.
def run(context):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    tbm = adsk.fusion.TemporaryBRepManager.get()
    X, Y, TOP = 0.0, 21.4, -0.39
    def env(m):
        m /= 10.0
        o = tbm.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create(X, Y, TOP + (0.65 + 2.65) / 2.0 - 0.0 + 0.0 if False else TOP + 0.65 + 1.0),
                 adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0), 1.235 + 2 * m, 0.65 + 2 * m, 2.0))
        c = tbm.createCylinderOrCone(adsk.core.Point3D.create(X, Y, TOP + 2.65), 0.225 + m, adsk.core.Point3D.create(X, Y, TOP + 6.0), 0.225 + m)
        tbm.booleanOperation(o, c, adsk.fusion.BooleanTypes.UnionBooleanType)
        return o
    bodies = []
    for b in root.bRepBodies:
        if b.isVisible and b.name != 'PCB': bodies.append(('root/' + b.name, b))
    for o in root.allOccurrences:
        if not o.isVisible: continue
        for b in o.bRepBodies:
            if b.isVisible and not (o.component.name == 'PCB_Review' and b.name.startswith('J5')):
                bodies.append((o.name + '/' + b.name, b))
    out = []
    for margin in (0, 1, 2, 3, 3.5, 4.0, 4.5, 5):
        e = env(margin)
        hits = []
        for nm, b in bodies:
            bb = b.boundingBox; eb = e.boundingBox
            if bb.maxPoint.x < eb.minPoint.x or bb.minPoint.x > eb.maxPoint.x or bb.maxPoint.y < eb.minPoint.y or bb.minPoint.y > eb.maxPoint.y or bb.maxPoint.z < eb.minPoint.z or bb.minPoint.z > eb.maxPoint.z:
                continue
            t = tbm.copy(b); ee = tbm.copy(e)
            try:
                tbm.booleanOperation(t, ee, adsk.fusion.BooleanTypes.IntersectionBooleanType)
                if t.volume > 1e-9: hits.append('%s (%.1f mm3)' % (nm, t.volume * 1000))
            except Exception as ex:
                hits.append('%s (bool error %s)' % (nm, ex))
        out.append('margin %.1f mm: %s' % (margin, ', '.join(hits) if hits else 'clear'))
    print('\n'.join(out))
