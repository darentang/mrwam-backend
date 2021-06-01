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

from picamera import PiCamera
from stream import Stream

from obc import OBC

config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')
# obc = OBC(socketio)

# CORS(app, resources={r'/*': {"origins": '*'}})

# @app.after_request
# def after_request(response):
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
#     return response

# download_dir = 'download'
# FLASK CONFIG
# app.config["DEBUG"] = True
# app.config['SECRET_KEY'] = 'secret!'
# app.config['SQLALCHEMY_DATABASE_URI'] = config['db']['path']
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
# app.config['CORS_HEADERS'] = 'Content-Type'

# db.init_app(app)
# app.app_context().push()
# db.drop_all()
# db.create_all()

# cron = BackgroundScheduler()
# cron.start()

# atexit.register(lambda: cron.shutdown(wait=False))
# serial_alive = False

# stream = Stream(640, 480)

@app.route('/', methods=['GET'])
def main():
    take_image()

    return send_from_directory("download", "test.jpeg")

def take_image():
    with PiCamera() as camera:
        print("capturing image")
        time.sleep(2)
        camera.resolution = (1920, 1080)
        camera.capture("download/test.jpeg", format='jpeg')
        print("finish capturing image")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=3000, debug=True)