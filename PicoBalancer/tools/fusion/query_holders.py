import adsk.core, adsk.fusion
def run(context):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    out = []
    for o in root.occurrences:
        if '18650' not in o.name: continue
        t = o.transform2.translation
        out.append(f"{o.name}: grounded={o.isGrounded} t=({t.x*10:.2f},{t.y*10:.2f},{t.z*10:.2f}) joints={o.joints.count} asBuilt={o.asBuiltJoints.count} rigidGroups={o.rigidGroups.count if hasattr(o,'rigidGroups') else '-'}")
        for c in o.childOccurrences:
            ct = c.transform2.translation
            out.append(f"   child {c.name}: t=({ct.x*10:.2f},{ct.y*10:.2f},{ct.z*10:.2f}) grounded={c.isGrounded}")
    out.append('root joints: %d, asBuilt: %d, rigidGroups: %d' % (root.joints.count, root.asBuiltJoints.count, root.rigidGroups.count))
    for j in list(root.joints) + list(root.asBuiltJoints):
        try:
            out.append(f"  joint {j.name}: {j.occurrenceOne.name if j.occurrenceOne else None} <-> {j.occurrenceTwo.name if j.occurrenceTwo else None}")
        except Exception as e:
            out.append(f"  joint {j.name}: {e}")
    out.append('pending snapshot: %s' % des.snapshots.hasPendingSnapshot)
    print('\n'.join(out))
