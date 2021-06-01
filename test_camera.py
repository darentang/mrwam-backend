from picamera import PiCamera

import time

with PiCamera() as camera:
    camera.resolution = (1920, 1080)
    print("starting")
    camera.capture("download/test.png")
    print("ending")