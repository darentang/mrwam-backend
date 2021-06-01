source ../rpi/bin/activate
# gunicorn --bind 0.0.0.0:5000 --worker-class eventlet -w 1 server:app
gunicorn --bind 0.0.0.0:5000 --threads 10 -w 1 server:app