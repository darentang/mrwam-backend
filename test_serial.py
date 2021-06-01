import time
import serial
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler("download/gps.log", "w", "utf-8")
formatter = logging.Formatter("[%(asctime)s] %(name)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


ser = serial.Serial(
	port = '/dev/ttyS0',
	baudrate = 9600,
	timeout = 1
)

logger.info(f"Starting Serial")

while True:
    line = ser.readline()
    try:
        line = line.decode('utf-8').split(",")
    except:
        logger.info(f"wtf is this line {line.hex()}")
        continue

    if line[0] == "$GPGLL":
        logger.info(f"location {line[1]}{line[2]}, {line[3]}{line[4]}")
        logger.info(f"UTC time {line[5]}")
    if line[0] == "$GPGSA":
        i = 3
        while line[i] != "":
            if i == 14:
                break
            i += 1
        logger.info(f"There are currently {i-3} satellites visible")