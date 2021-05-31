import numpy as np
import time
import configparser
import serial

config = configparser.ConfigParser()
config.read('config.ini')

lat = float(config['gps']['lat'])
lon = float(config['gps']['lon'])



class OBC:
    def __init__(self, sio):
        self.socketio = sio
        self.gps = serial.Serial(
            port=config['gps']['port'], 
            baudrate=int(config['gps']['baudrate']),
            timeout=float(config['gps']['timeout'])
        )
        print("gps serial established")

    def obc_loop(self):
        while True:
            # obc code here
            self.broadcast_wod()

            
            if self.gps.in_waiting > 30:
                print(self.gps.readline())

            # can change
            time.sleep(1)



    def broadcast_wod(self):
        self.socketio.emit('wod', {
            'time': time.time(),
            'lat': lat  + np.random.normal(),
            'lon': lon  + np.random.normal(),
            'mode': 'normal',
            "v_batt": 4.5 + np.random.normal(),
            "i_batt": 400.2  + np.random.normal(),
            "v_33": 254.2  + np.random.normal(),
            "v_5": 3.852  + np.random.normal(),
            "t_comm": 25.0  + np.random.normal(),
            "t_eps": 29.6  + np.random.normal(),
            "t_batt": 28.6  + np.random.normal()
        })
        