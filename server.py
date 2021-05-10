import flask
from flask import Flask
from flask import request
from flask import send_from_directory
import atexit
from flask_cors import CORS, cross_origin

import os
import time
import datetime
from model import Job, db
from apscheduler.schedulers.background import BackgroundScheduler
import uuid



app = Flask(__name__)
CORS(app, resources={r'/*': {"origins": '*'}})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    return response

download_dir = 'download'
app.config["DEBUG"] = True
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/user.db'
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


lat = -33.8688
lon = 151.2093

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
            'created_time': os.stat(path).st_ctime,
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
        # cron.add_job(
        #     func=take_image, args=([job.id]), trigger="date", run_date=datetime.datetime.now(),
        #     id=str(job.id)            
        #     )

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
    jobs = Job.query.all()
    res = []
    for job in jobs:
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


if __name__ == '__main__':
    app.run(port=5000,debug=True) 