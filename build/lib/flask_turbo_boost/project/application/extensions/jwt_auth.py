import jwt
import datetime
from functools import wraps
from application.models import db, User
from flask import current_app, request, g, abort, jsonify


def identity(token_or_payload):
    payload = _ensure_decode(token_or_payload)

    user_id = payload.get('user_id')
    return User.find(id=user_id, active=True)


def is_expired_token(token_or_payload):
    payload = _ensure_decode(token_or_payload)

    now = datetime.datetime.now()
    exp_date = payload.get('expired_date')
    if exp_date:
        expired_date = _convert_datestring_to_dateobject(exp_date)
        return now > expired_date
    else:
        raise Exception('Cannot get expired date in token')


def required_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('token', None)
        if token:
            user = identity(token)
            if user:
                g.user = user
                return f(*args, **kwargs)

        return abort(401)
    return wrapper


def generate_token(user_id):
    payload = dict(user_id=user_id, type='access')
    expired_date = datetime.datetime.now() + datetime.timedelta(minutes=current_app.config.get('JWT_EXPIRED_IN_MIN'))
    payload['expired_date'] = str(expired_date)
    return encode(payload)


def generate_refresh_token(user_id):
    payload = dict(user_id=user_id, type='refresh')
    expired_date = datetime.datetime.now() + datetime.timedelta(days=current_app.config.get('JWT_REFRESH_EXPIRED_IN_DAY'))
    payload['expired_date'] = str(expired_date)
    return encode(payload)


def encode(payload):
    return jwt.encode(payload, current_app.config.get('JWT_SECRET_KEY'),
            algorithm=current_app.config.get('JWT_ALGOR')).decode('utf-8')


def decode(token):
    payload = jwt.decode(token, current_app.config.get('JWT_SECRET_KEY'),
            algorithm=current_app.config.get("JWT_ALGOR"))
    return payload


def valid_refresh_token(refresh_token):
    payload = ensure_decode(refresh_token)
    return identity(payload) and not is_expired_token(payload) and payload.get('type') == 'refresh'


def valid_registration_token(registration_token):
    payload = ensure_decode(registration_token)
    return payload.get('type') == 'registration' and registration_identity(payload)


def get_user_from_token(token):
    payload = decode(token)
    user = identity(payload)
    return user


def _convert_datestring_to_dateobject(datestring):
    dt, msec = datestring.split('.')
    date, time = dt.split(' ')
    return datetime.datetime(*map(lambda x: int(x), list(date.split('-') + time.split(':'))))


def _ensure_decode(token_or_payload):
    if type(token_or_payload) is not dict:
        payload = decode(token_or_payload)
    else:
        payload = token_or_payload

    return payload
