from picamera import PiCamera

import time

camera = PiCamera()
camera.resolution = (1920, 1080)


time.sleep(2)
camera.capture("download/test.png")
camera.close()