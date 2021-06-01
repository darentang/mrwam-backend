import numpy as np
import time
import configparser
import serial

config = configparser.ConfigParser()
config.read('config.ini')

class OBC:
    def __init__(self, sio):
        self.socketio = sio
        self.gps = serial.Serial(
            port=config['gps']['port'], 
            baudrate=int(config['gps']['baudrate']),
            timeout=float(config['gps']['timeout'])
        )

        self.lat = float(config['gps']['lat'])
        self.lon = float(config['gps']['lon'])
        print(f"gps serial established, baudrate {config['gps']['baudrate']}, timeout {config['gps']['timeout']}")

    def gps_loop(self):
        while True:
            line = self.gps.readline()
            try:
                line = line.decode('utf-8').split(",")
            except:
                continue

            if line[0] == "$GPGLL":
                lat = float(line[1])/100
                lon = float(line[3])/100

                if line[2] == "S":
                    lat *= -1

                if line[4] == "W":
                    lon *= -1
            time.sleep(0.1)

    def obc_loop(self):
        while True:
            # obc code here
            self.broadcast_wod()

            # can change
            time.sleep(1)



    def broadcast_wod(self):
        self.socketio.emit('wod', {
            'time': time.time(),
            'lat': self.lat,
            'lon': self.lon,
            'mode': 'normal',
            "v_batt": 4.5 + np.random.normal(),
            "i_batt": 400.2  + np.random.normal(),
            "v_33": 254.2  + np.random.normal(),
            "v_5": 3.852  + np.random.normal(),
            "t_comm": 25.0  + np.random.normal(),
            "t_eps": 29.6  + np.random.normal(),
            "t_batt": 28.6  + np.random.normal()
        })
        