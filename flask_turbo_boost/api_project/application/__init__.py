# coding: utf-8

import sys
import os

# Insert project root path to sys.path
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

import time
import logging
from flask import Flask, request, url_for, g, render_template, session
from flask_wtf.csrf import CSRFProtect
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.contrib.fixers import ProxyFix
from six import iteritems
from flask_security.core import current_user, AnonymousUser
from config import load_config

# convert python's encoding to utf8
try:
    from imp import reload

    reload(sys)
    sys.setdefaultencoding('utf8')
except (AttributeError, NameError):
    pass


def create_app():
    """Create Flask app."""
    config = load_config()

    app = Flask(__name__)
    app.config.from_object(config)

    # Proxy fix
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # ensure instance path exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register components
    register_logs(app)
    register_db(app)
    register_security(app)
    register_routes(app)
    register_error_handle(app)
    register_hooks(app)

    register_scripts(app)
    register_shell_context(app)

    return app


def register_logs(app):
    from .utils.sentry import sentry

    if app.testing:
        app.logger.setLevel(logging.DEBUG)
        return

    if app.debug:
        # DebugToolbarExtension(app)
        app.logger.setLevel(logging.DEBUG)

    if os.environ.get('MODE') == 'PRODUCTION':
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.ERROR)
        # if set gunicorn
        gunicorn_logger = logging.getLogger('gunicorn.error')
        if gunicorn_logger:
            app.logger.handlers = gunicorn_logger.handlers
            app.logger.setLevel(gunicorn_logger.level)

        # sentry for production
        if app.config.get('SENTRY_DSN'):
            app.logger.info('SENTRY active')
            sentry.init_app(app, dsn=app.config.get('SENTRY_DSN'),
                    logging=True, level=logging.ERROR)
    else:
        # enable sentry for development
        if app.config.get('SENTRY_DSN'):
            app.logger.info('SENTRY is enable')
            sentry.init_app(app, dsn=app.config.get('SENTRY_DSN'))


def register_security(app):
    from flask_security import SQLAlchemyUserDatastore, Security
    from .models import db, User, Role

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)
    from flask import session

    @app.before_request
    def before_request():
        g.user = current_user
        if g.user is not None and g.user.has_role('admin'):
           g._before_request_time = time.time()

    @app.after_request
    def after_request(response):
        if hasattr(g, '_before_request_time'):
            delta = time.time() - g._before_request_time
            response.headers['X-Render-Time'] = delta * 1000
        return response


def register_db(app):
    """Register models."""
    from .models import db

    db.init_app(app)


def register_routes(app):
    """Register routes."""
    from .controllers import api_v1
    from flask.blueprints import Blueprint

    for module in _import_submodules_from_package(api_v1):
        bp = getattr(module, 'bp')
        if bp and isinstance(bp, Blueprint):
            app.register_blueprint(bp)


def register_error_handle(app):
    """Register HTTP error pages."""

    @app.errorhandler(403)
    def page_403(error):
        return render_template('site/403/403.html'), 403

    @app.errorhandler(404)
    def page_404(error):
        return render_template('site/404/404.html'), 404

    @app.errorhandler(500)
    def page_500(error):
        return render_template('site/500/500.html'), 500


def register_hooks(app):
    pass


def register_scripts(app):
    # init migration script
    from flask_migrate import Migrate
    from .models import db
    Migrate(app, db)

    from scripts.seed import seed_cli
    app.cli.add_command(seed_cli)


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        from .models import db
        import application.models as m

        return dict(app=app, db=db, m=m)


def _get_template_name(template_reference):
    """Get current template name."""
    return template_reference._TemplateReference__context.name


def _import_submodules_from_package(package):
    import pkgutil

    modules = []
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__,
                                                         prefix=package.__name__ + "."):
        modules.append(__import__(modname, fromlist="dummy"))
    return modules


# API Register Helpers -----------------------------------------------------------------

def register_allow_origin(app):
    @app.after_request
    def after_request(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Credentials'] = True
        response.headers['Access-Control-Allow-Methods'] = 'PUT, DELETE, GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Access-Token,DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Length,Content-Range'
        return response


def register_jsonencoder(app):
    from flask.json import JSONEncoder
    from datetime import datetime, date, time
    from decimal import Decimal
    import enum

    class CustomJSONEncoder(JSONEncoder):
        def default(self, obj):
            try:
                if isinstance(obj, datetime):
                    # if obj.utcoffset() is not None:
                    #    obj = obj - obj.utcoffset()
                    return obj.astimezone(timezone('Asia/Bangkok')).isoformat()
                if isinstance(obj, date):
                    return str(obj.isoformat())
                if isinstance(obj, Decimal):
                    return str(obj)
                if isinstance(obj, enum.Enum):
                    return str(obj.value)
                if isinstance(obj, time):
                    return str(obj)
                iterable = iter(obj)
            except TypeError:
                pass
            return JSONEncoder.default(self, obj)

    app.json_encoder = CustomJSONEncoder


def create_celery(app=None):
    app = app or create_app()

    celery = Celery(
                app.import_name,
                backend=app.config.get('RESULT_BACKEND'),
                broker=app.config.get('BROKER_URL'),
                timezone='Asia/Bangkok')

    celery.conf.update(task_always_eager=False)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
