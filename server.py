import eventlet
eventlet.monkey_patch()


import flask
from flask import Flask
from flask import request
from flask import send_from_directory
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

from obc import OBC

config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')
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



lat = float(config['gps']['lat'])
lon = float(config['gps']['lon'])

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

def take_image(job_id):
    app.app_context().push()
    fname = str(uuid.uuid4()) + '.txt'
    job = Job.query.get(job_id)
    with open(os.path.join(download_dir, fname), 'w') as f:
        f.write(str(job))
    job.image_name = fname
    job.completed = True
    db.session.commit()


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

@app.route('/wod', methods=['GET'])
@cross_origin()
def wod():
    return {
        'time': time.time(),
        'lat': lat,
        'lon': lon,
        'mode': 'normal',
        "v_batt": 4.5 ,
        "i_batt": 400.2,
        "v_33": 254.2,
        "v_5": 3.852,
        "t_comm": 25.0,
        "t_eps": 29.6,
        "t_batt": 28.6
    }

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
    try:
        arduino = serial.Serial(
            port=config['serial']['port'], 
            baudrate=int(config['serial']['baudrate']), 
            timeout=float(config['serial']['timeout'])
            )
    except Exception:
        print("error connecting to serial")
        return
    if arduino.isOpen():
        arduino.close()
    arduino.open()
    serial_alive = True
    print("Serial open")
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

def serial_read_callback(msg):
    try:
        q = np.array(list(map(float, msg.decode().split())))
        eul = quat_to_eul(q)
        socketio.emit('eul', {'x': eul[0], 'y': eul[1], 'z': eul[2]})
    except Exception as e:
        print("err", msg)
        pass
    

serial_thread = threading.Thread(target=serial_event)
serial_thread.setDaemon(True)
serial_thread.start()
obc_thread = threading.Thread(target=obc.obc_loop)
obc_thread.setDaemon(True)
obc_thread.start()

if __name__ == '__main__':
    socketio.run(app, port=5000, debug=False) 