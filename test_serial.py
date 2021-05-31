import time
import serial
import logging

logging.basicConfig(filename="download/gps.log", encoding="utf-8", level=logging.DEBUG)

ser = serial.Serial(
	port = '/dev/ttyS0',
	baudrate = 9600,
	timeout = 1
)

while True:
    line = ser.readline()
    try:
        line = line.encode('utf-8').split(",")
    except:
        continue

    if line[0] == "$GPGLL":
        logging.info(f"Recorded location {line[1]}E, {line[3]}N")
    if line[0] == "$GPGSA":
        i = 3
        while line[i] != "":
            if i == 14:
                break
            i += 1
        logging.info(f"There are currently {i-3} satellites visible")