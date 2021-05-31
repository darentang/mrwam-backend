import time
import serial

ser = serial.Serial(
	port = '/dev/ttyS0',
	baudrate = 9600,
	timeout = 1
)

while True:
    print(ser.readline())

    time.sleep(1)