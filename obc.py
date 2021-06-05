import numpy as np
import time
import configparser
import serial

config = configparser.ConfigParser()
config.read('config.ini')

class OBC:
    def __init__(self, sio):
        self.socketio = sio
        try:
            self.gps = serial.Serial(
                port=config['gps']['port'], 
                baudrate=int(config['gps']['baudrate']),
                timeout=float(config['gps']['timeout'])
            )
        except:
            print("error connecting to gps")
            self.gps = None
        else:
            print(f"gps serial established, baudrate {config['gps']['baudrate']}, timeout {config['gps']['timeout']}")
            
        self.lat = float(config['gps']['lat'])
        self.lon = float(config['gps']['lon'])
        self.wod = [0, 0, 0, 0, 0, 0, 0]
        

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
            "v_batt": self.wod[0] / 1000,
            "i_batt": self.wod[1],
            "v_33": self.wod[2],
            "v_5": self.wod[3],
            "t_comm": self.wod[4],
            "t_eps": self.wod[5],
            "t_batt": self.wod[6]
        })
        