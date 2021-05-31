import serial
import time

ser = serial.Serial(port="/dev/ttyS0", baudrate=9600, timeout=0.1)

while True:
    print(ser.readline())