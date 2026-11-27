import adsk.core, adsk.fusion
def run(context):
    des = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    root = des.rootComponent
    j = root.joints.itemByName('Rigid 6')
    out = ['type %s, motion %s' % (type(j).__name__, j.jointMotion.jointType)]
    for k, g in (('one', j.geometryOrOriginOne), ('two', j.geometryOrOriginTwo)):
        nm = type(g).__name__
        try:
            o = g.origin if hasattr(g, 'origin') else g.geometry.origin
            out.append('%s: %s origin (%.2f, %.2f, %.2f) mm' % (k, nm, o.x*10, o.y*10, o.z*10))
        except Exception as e:
            out.append('%s: %s (%s)' % (k, nm, e))
        try:
            out.append('   entity: %s' % type(g.entityOne).__name__)
        except Exception:
            pass
    try:
        out.append('offset param: %s' % j.offset.expression)
    except Exception as e:
        out.append('offset: %s' % e)
    print('\n'.join(out))
