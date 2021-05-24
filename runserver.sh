# gunicorn --certfile=server.crt --keyfile=server.key --bind 0.0.0.0:5000 server:app
gunicorn --certfile=server.crt --keyfile=server.key --bind 0.0.0.0:5000 --worker-class eventlet -w 1 server:app