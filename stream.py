import io
try:
    from picamera import PiCamera
except ImportError:
    print("error importing picamera")
import time
import threading

class Stream:
    def __init__(self, width, height):
        self.last_access = 0
        self.frame = None
        self.width = width
        self.height = height
        self.last_access = time.time()

        self.thread = threading.Thread(target=self.feed_generator)
        self.thread.start()
        self.ready = False

    def feed_generator(self):
        print("starting video feed thread")
        while True:
            if time.time() - self.last_access > 10:
                continue
            time.sleep(3)
            with PiCamera() as camera:
                camera.resolution = (self.width, self.height)
                stream = io.BytesIO()
                print("starting stream")
                for frame in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
                    self.ready = True
                    stream.seek(0)
                    self.frame = stream.read()
                    stream.seek(0)
                    stream.truncate()
                    time.sleep(0.1)
                    if time.time() - self.last_access > 10:
                        stream.ready = False
                        print("exiting stream")
                        break
            time.sleep(1)

    def get_frame(self):
        self.last_access = time.time()
        return self.frame


if __name__ == "__main__":
    stream = Stream(640, 480)
    while not stream.ready:
        continue
    with open("test.jpeg", "wb") as f:
        f.write(stream.get_frame())
    print(stream.get_frame())
    print(stream.get_frame())
    print(stream.get_frame())