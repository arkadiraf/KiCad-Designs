import adsk.core, adsk.fusion
def run(context):
    des = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    b = des.rootComponent.bRepBodies.itemByName('Battery Cover')
    out = []
    for f in b.faces:
        g = f.geometry
        if g.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType and abs(g.normal.z) > 0.99:
            bb = f.boundingBox
            out.append('plane z=%.2f normal %+.0f area %.1f mm2 x[%.2f,%.2f] y_f[%.2f,%.2f]' % (bb.minPoint.z*10, g.normal.z, f.area*100, bb.minPoint.x*10, bb.maxPoint.x*10, bb.minPoint.y*10, bb.maxPoint.y*10))
    print('\n'.join(sorted(out)))
