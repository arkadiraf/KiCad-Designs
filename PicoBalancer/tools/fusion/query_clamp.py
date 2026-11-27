import adsk.core, adsk.fusion
def run(context):
    des = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    root = des.rootComponent
    out = []
    def show(name, b):
        bb = b.boundingBox
        out.append('%s | %s vis=%s x[%.2f,%.2f] y_f[%.2f,%.2f] z[%.2f,%.2f]' % (name, b.name, b.isVisible, bb.minPoint.x*10, bb.maxPoint.x*10, bb.minPoint.y*10, bb.maxPoint.y*10, bb.minPoint.z*10, bb.maxPoint.z*10))
        for f in b.faces:
            g = f.geometry
            if g.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType and abs(g.axis.z) > 0.99 and g.radius < 0.3:
                fb = f.boundingBox
                out.append('     hole r=%.3f at (%.2f, %.2f) z[%.2f,%.2f]' % (g.radius*10, g.origin.x*10, g.origin.y*10, fb.minPoint.z*10, fb.maxPoint.z*10))
    for b in root.bRepBodies: show('ROOT', b)
    for o in root.allOccurrences:
        if any(k in o.name for k in ('18650', 'PCB_Review', 'Micro-Motor', 'pololu', 'magnetic', 'Bracket', 'TAU')): continue
        for b in o.bRepBodies: show(o.fullPathName, b)
    print('\n'.join(out))
