import adsk.core, adsk.fusion
def run(context):
    app = adsk.core.Application.get()
    vp = app.activeViewport
    cam = vp.camera
    cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    cam.target = adsk.core.Point3D.create(0, 12.1, 0)
    cam.eye = adsk.core.Point3D.create(0, 12.1, 60)
    cam.upVector = adsk.core.Vector3D.create(0, 1, 0)
    cam.isFitView = False
    cam.viewExtents = 13.0
    vp.camera = cam
    vp.refresh()
    print('camera set: top view')
