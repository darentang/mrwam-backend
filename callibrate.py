import configparser
import serial
import numpy as np
from scipy.optimize import leastsq


config = configparser.ConfigParser()
config.read('config.ini')


ser = serial.Serial(
	port = config['serial']['port'],
	baudrate = int(config['serial']['baudrate']),
	timeout = float(config['serial']['timeout'])
)

ms = []

for i in range(300):
    data = ser.readline().decode().rstrip().lstrip().split(" ")
    g = list(map(float, data[1:4]))
    a = list(map(float, data[5:8]))
    m = list(map(float, data[9:]))
    print(i, m)
    if len(m) == 3:
        ms.append(m)
ms = np.array(ms)

np.savetxt("data.csv", np.array(ms), delimiter=",")

def fitfunc(p, coords):
    x0, y0, z0, R = p
    x, y, z = coords.T
    return np.sqrt((x-x0)**2 + (y-y0)**2 + (z-z0)**2)

p0 = [0, 0, 0, 1]



errfunc = lambda p, x: fitfunc(p, x) - p[3]
p1, flag = leastsq(errfunc, p0, args=(ms,))
print(p1)
np.savetxt("mag-offset.csv", p1, delimiter=",")
