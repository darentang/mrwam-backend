from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    time = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    image_name = db.Column(db.String(20), default="")

    def __repr__(self):
        return f"Job at lat: {self.lat}, lon: {self.lon} at {self.time.strftime('%m/%d/%Y, %H:%M:%S')} UTC"