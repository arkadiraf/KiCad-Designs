import adsk.core, adsk.fusion
def run(context):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    for o in root.allOccurrences:
        if 'Base' not in o.name: continue
        for b in o.bRepBodies:
            for f in b.faces:
                g = f.geometry
                if g.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType:
                    bb = f.boundingBox
                    if bb.minPoint.z*10 < -4.0:
                        c = g.origin
                        print(f"{o.name[:40]} cyl r={g.radius*10:.3f} axis({g.axis.x:.0f},{g.axis.y:.0f},{g.axis.z:.0f}) bb x[{bb.minPoint.x*10:.2f},{bb.maxPoint.x*10:.2f}] y[{bb.minPoint.y*10:.2f},{bb.maxPoint.y*10:.2f}] z[{bb.minPoint.z*10:.2f},{bb.maxPoint.z*10:.2f}]")
    print('appearances in design:', des.appearances.count)
    lib = app.materialLibraries.itemByName('Fusion Appearance Library')
    print('lib', lib is not None)
