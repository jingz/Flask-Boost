# coding: utf-8
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ._base import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    avatar = db.Column(db.String(200), default='default.png')
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    confirm_at = db.Column(db.DateTime)

    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # relationship
    roles = db.relationship("Role", secondary="users_roles", backref='users')

    def __repr__(self):
        return '<User %s>' % self.name
