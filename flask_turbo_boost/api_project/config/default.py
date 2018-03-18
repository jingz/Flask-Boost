# coding: utf-8
import os


class Config(object):
    """Base config class."""
    # Flask app config
    DEBUG = False
    TESTING = False
    SECRET_KEY = "\xb5\xb3}#\xb7A\xcac\x9d0\xb6\x0f\x80z\x97\x00\x1e\xc0\xb8+\xe9)\xf0}"
    PERMANENT_SESSION_LIFETIME = 3600 * 24 * 7
    SESSION_COOKIE_NAME = '#{project}_session'

    # Root path of project
    PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Site domain
    SITE_TITLE = "#{project|title}"
    SITE_DOMAIN = "http://localhost:5000"

    # WTForm config
    # WTF_CSRF_ENABLED = False

    # SQLAlchemy config
    # See:
    # https://pythonhosted.org/Flask-SQLAlchemy/config.html#connection-uri-format
    # http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html#database-urls
    SQLALCHEMY_DATABASE_URI = "postgresql://user:password@host/database"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask Security
    # https://pythonhosted.org/Flask-Security/configuration.html
    # SECURITY_PASSWORD_HASH
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False
    SECURITY_LOGIN_WITHOUT_CONFIRMATION = False
    SECURITY_PASSWORD_SALT = '\xc7F\xcce\x03\xc3\x02_\x04\x1e@\x9fC\xf7'
    # api auth
    # SECURITY_TOKEN_AUTHENTICATION_HEADER = 'x-access-token'

    # Flask-DebugToolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # Sentry config
    SENTRY_DSN = ''

    # Host string, used by fabric
    HOST_STRING = "root@12.34.56.78"
