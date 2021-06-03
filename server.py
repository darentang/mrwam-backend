# import eventlet
# eventlet.monkey_patch()

import flask
from flask import Flask, request, Response, send_from_directory
import atexit
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, send, emit

import os
import time
import datetime
from model import Job, db
from apscheduler.schedulers.background import BackgroundScheduler
import uuid

import serial
import threading
import numpy as np

import configparser

try:
    from picamera import PiCamera
except ImportError:
    print("error importing picamera")
from stream import Stream

from obc import OBC

config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode="threading")
obc = OBC(socketio)

CORS(app, resources={r'/*': {"origins": '*'}})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    return response

download_dir = 'download'
# FLASK CONFIG
app.config["DEBUG"] = True
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = config['db']['path']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
app.config['CORS_HEADERS'] = 'Content-Type'

db.init_app(app)
app.app_context().push()
# db.drop_all()
db.create_all()

cron = BackgroundScheduler()
cron.start()

atexit.register(lambda: cron.shutdown(wait=False))
serial_alive = False

# stream = Stream(640, 480)

eul = np.array([0 ,0, 0])

try:
    arduino = serial.Serial(
        port=config['serial']['port'], 
        baudrate=int(config['serial']['baudrate']), 
        timeout=float(config['serial']['timeout'])
        )
    if arduino.is_open:
        arduino.close()
    arduino.open()
except Exception as e:
    arduino = None
    print("error connecting to serial", e)


@app.route('/list_downloads', methods=['GET'])
@cross_origin()
def list_downloads():
    # return a list of downloadable files including their ID, name, size, date of creation
    d = []
    # get list of images, use i as id
    for i, fname in enumerate(os.listdir(download_dir)):
        path = os.path.join(download_dir, fname)
        d.append({
            'filename': fname,
            'size': os.stat(path).st_size,
            'created_time': os.stat(path).st_mtime,
        })
    # return json of files
    return {'files': d}

@app.route('/download', methods=['GET'])
@cross_origin()
def download():
    # id_ is a string
    name = request.args.get('name')
    
    path = os.path.join(download_dir, name)
    print(path)
    if os.path.exists(path):
        return send_from_directory(download_dir, name)


    # else you dont return anything
    return {'success': False}


@app.route('/add_job', methods=['POST'])
@cross_origin()
def schedule():
    print(request.json)
    try:
        lat = float(request.json.get('lat'))
        lon = float(request.json.get('lon'))
        time = float(request.json.get('time'))
        time = datetime.datetime.fromtimestamp(time)
    except Exception as e:
        return {'success': False, 'message': str(e)}


    # check scheduling conflict etc
    if True:
        job = Job(lat=lat, lon=lon, time=time)
        db.session.add(job)
        db.session.commit()

        cron.add_job(func=take_image, args=([job.id]), trigger="date", run_date=time, id=str(job.id))

        return {
            'success': True, 'message': str(job), 'job_id': job.id
            }

@app.route('/delete_job', methods=['GET'])
@cross_origin()
def delete_schedule():
    id_ = int(request.args.get('id'))
    job = Job.query.get(id_)
    db.session.delete(job)
    if not job.completed:
        try:
            cron.remove_job(str(job.id))
        except:
            pass
    db.session.commit()
    return {'success': True}

@app.route('/take_image_now', methods=['GET'])
@cross_origin()
def take_image_now():
    take_image(None)
    return {'success': True}

def take_image(job_id):
    app.app_context().push()
    fname = str(uuid.uuid4()) + '.png'
    if job_id != None:
        job = Job.query.get(job_id)
        job.image_name = fname
        job.completed = True
        db.session.commit()
    print(f"taking image now with filename {fname}")

    with PiCamera() as camera:
        camera.start_preview()
        time.sleep(2)
        camera.resolution = (int(config['camera']['width']), int(config['camera']['height']))
        camera.capture(os.path.join(download_dir, fname), format='png')
    
    print("finished capturing")

def gen_feed():
    while True:
        frame = stream.get_frame()
        if frame is None:
            frame = b''
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
@cross_origin()
def video_feed():
    return Response(gen_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/test_motor', methods=['GET'])
@cross_origin()
def test_motor():
    axis = request.args.get('axis')
    direction = request.args.get('direction')

    motor_map = {
        ("X", "pos"): "X",
        ("Y", "pos"): "Y",
        ("Z", "pos"): "Z",
        ("X", "neg"): "x",
        ("Y", "neg"): "y",
        ("Z", "neg"): "z",
    }

    code = motor_map.get((axis, direction), "X")
    print(code)
    arduino.write((code + "\n").encode("utf-8"))
    return {'success': True}


@app.route('/point', methods=['GET'])
@cross_origin()
def point():
    mode = request.args.get('mode')
    if mode == "Q":
        arduino.write((mode + "\n").encode("utf-8"))
        return {'success': True}

    axis_map = {
        "X": 0, "Y":1, "Z":2
    }

    axis = request.args.get('axis')

    eul[axis_map[axis]] += np.deg2rad(5)

    q = eul_to_quat(eul)

    arduino.write((f"q {q[0]:.3f} {q[1]:.3f} {q[2]:.3f} {q[3]:.3f}\n").encode("utf-8"))
    return {'success': True}

@app.route('/list_schedule', methods=['GET'])
@cross_origin()
def list_schedule():
    jobc = Job.query.all()
    res = []
    for job in jobc:
        res.append(
            {
            'id': job.id, 'lat': job.lat, 'lon': job.lon, 'time': job.time.timestamp(), 
            'completed': job.completed, 'image_name': job.image_name
            }
        )
    return {'list': res}

@app.route('/check_connection', methods=['GET'])
@cross_origin()
def check_connection():
    return{'success': True}

@app.route('/', methods=['GET'])
@cross_origin()
def test():
    return "<h1>The Server is Working</h1>"

def serial_event():
    global serial_alive
    if serial_alive:
        return
    serial_alive = True
    print("Serial open")

    if arduino is None:
        return
    while True:
        try:    
            b = arduino.readline()
            if b != b'':
                serial_read_callback(b)
        except Exception as e:
            print("error reading line", e)
            pass



def quat_to_eul(q):
    return np.array([
        np.arctan2(2*(q[0]*q[1]+q[2]*q[3]), 1-2*(q[1]**2+q[2]**2)),
        np.arcsin(2*(q[0]*q[2]-q[3]*q[1])),
        np.arctan2(2*(q[0]*q[3]+q[1]*q[2]), 1-2*(q[2]**2+q[3]**2))
    ])

def eul_to_quat(e):
    roll = e[0]
    pitch = e[1]
    yaw = e[2]
    qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
    qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
    qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
    qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)

    return np.array([qw, qx, qy, qz])


def serial_read_callback(msg):
    print(msg)
    global eul
    try:
        msg = msg.decode().split()
    except:
        print("err", msg)
        return
    if msg[0] == "q":
        try:
            q = np.array(list(map(float, msg[1:])))
            eul = quat_to_eul(q)
            socketio.emit('eul', {'x': eul[0], 'y': eul[1], 'z': eul[2]})
        except Exception as e:
            print("err", msg)
    if msg[0] == "T":
        return

serial_thread = threading.Thread(target=serial_event, daemon=True)
serial_thread.start()

obc_thread = threading.Thread(target=obc.obc_loop, daemon=True)
obc_thread.start()

# gps_thread = threading.Thread(target=obc.gps_loop)
# gps_thread.start()

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=False) 