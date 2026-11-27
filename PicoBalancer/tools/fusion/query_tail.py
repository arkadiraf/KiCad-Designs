import adsk.core, adsk.fusion
def run(context):
    des = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    root = des.rootComponent; tl = des.timeline
    occ = [o for o in root.occurrences if o.name == '18650_LI-ON_Battery_Holder_1042P v2:1'][0]
    j = root.joints.itemByName('Rigid 6')
    print('tail: ' + ' | '.join(tl.item(i).name for i in range(36, tl.count)) + '  || left grounded=%s Rigid6 suppressed=%s/%s review=%s' % (
        occ.isGrounded, j.isSuppressed, j.timelineObject.isSuppressed, any(o.name.startswith('PCB_Review') for o in root.occurrences)))
