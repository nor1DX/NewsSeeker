from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    link = db.Column(db.String, nullable=False, unique=True)
    published = db.Column(db.DateTime, nullable=False)
    source = db.Column(db.String, nullable=False)


def init_db():
    db.create_all()
