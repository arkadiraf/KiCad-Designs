import adsk.core, adsk.fusion
def run(context):
    des = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    j = des.rootComponent.joints.itemByName('Rigid 6')
    out = []
    for nm in ('offsetX', 'offsetY', 'offsetZ', 'angle', 'isFlipped'):
        try:
            v = getattr(j, nm)
            out.append('%s = %s' % (nm, v.expression if hasattr(v, 'expression') else v))
        except Exception as e:
            out.append('%s: n/a (%s)' % (nm, e))
    g = j.geometryOrOriginTwo
    try:
        out.append('two primary %s secondary %s' % (tuple(round(c, 3) for c in g.primaryAxisVector.asArray()), tuple(round(c, 3) for c in g.secondaryAxisVector.asArray())))
    except Exception as e:
        out.append('axes: %s' % e)
    print('\n'.join(out))
