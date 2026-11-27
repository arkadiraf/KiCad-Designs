import adsk.core, adsk.fusion
def run(context):
    app = adsk.core.Application.get()
    vp = app.activeViewport
    cam = vp.camera
    cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    cam.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
    cam.isFitView = True
    vp.camera = cam
    vp.fit()
    vp.refresh()
    print('camera set: iso top right, fit')
