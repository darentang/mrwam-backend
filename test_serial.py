import time
import serial
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler("download/gps.loh", "w", "utf-8")
formatter = logging.Formatter("%(name)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


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
        logger.info(f"Recorded location {line[1]}E, {line[3]}N")
    if line[0] == "$GPGSA":
        i = 3
        while line[i] != "":
            if i == 14:
                break
            i += 1
        logger.info(f"There are currently {i-3} satellites visible")