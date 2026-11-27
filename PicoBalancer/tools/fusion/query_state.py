import adsk.core, adsk.fusion
def run(context):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    out = ['occurrences: ' + ', '.join(o.name for o in root.occurrences)]
    for o in root.occurrences:
        if '18650' in o.name:
            bodies = [b for c in o.childOccurrences for b in c.bRepBodies]
            if bodies:
                bb = bodies[0].boundingBox
                out.append('  %s grounded=%s first body x[%.2f,%.2f] y_f[%.2f,%.2f]' % (o.name, o.isGrounded, bb.minPoint.x*10, bb.maxPoint.x*10, bb.minPoint.y*10, bb.maxPoint.y*10))
    tl = des.timeline
    out.append('timeline %d: ' % tl.count + ' | '.join('%d %s%s' % (i, tl.item(i).name, ' (S)' if tl.item(i).isSuppressed else '') for i in range(tl.count)))
    j = root.joints.itemByName('Rigid 6'); out.append('Rigid 6 suppressed=%s' % (j.timelineObject.isSuppressed if j else 'missing'))
    print('\n'.join(out))
