from . import db
from flask_login import UserMixin
from datetime import datetime

class HiddenPosts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(150))

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    by = db.Column(db.String(100))
    link = db.Column(db.String(900))
    desc = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.now())

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    room = db.Column(db.String(10))
    by = db.Column(db.String(10))
    to = db.Column(db.String(10))
    message = db.Column(db.String(500))
    time = db.Column(db.DateTime, default=datetime.now())
