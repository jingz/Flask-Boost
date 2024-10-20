# coding: utf-8
from flask_security import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ._base import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    avatar = db.Column(db.String(200), default='default.png')
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    confirm_at = db.Column(db.DateTime)

    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Social Auth Provider, Facebook, Google
    auth_provider_id = db.Column(db.String(255))
    auth_provider_user_id = db.Column(db.String(255))
    auth_provider_profile_pic = db.Column(db.String(512))
    auth_provider_access_token = db.Column(db.String(255))
    auth_provider_secret = db.Column(db.String(255))

    # relationship
    roles = db.relationship("Role", secondary="users_roles", backref='users')

    def __repr__(self):
        return '<User %s>' % self.name
