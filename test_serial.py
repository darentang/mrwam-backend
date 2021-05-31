import serial
import time

ser = serial.Serial(port="/dev/ttyS0", baudrate=115200)

while True:
    print(ser.readlines())