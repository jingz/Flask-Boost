# coding: utf-8
import sys
import os

# Insert project root path to sys.path
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

import time
import logging
from flask import Flask, request, url_for, g, render_template, session, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.contrib.fixers import ProxyFix
from six import iteritems
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

    # CSRF protect
    # CSRFProtect(app)

    if app.debug or app.testing:
        DebugToolbarExtension(app)
    else:
        # Log errors to stderr in production mode
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.ERROR)

        # Enable Sentry
        if app.config.get('SENTRY_DSN'):
            from .utils.sentry import sentry

            sentry.init_app(app, dsn=app.config.get('SENTRY_DSN'))

    # Register components
    register_db(app)
    register_routes(app)
    register_error_handle(app)
    # register_hooks(app)

    return app


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
        return jsonify(dict(code=403, message="Forbidden")), 403

    @app.errorhandler(404)
    def page_404(error):
        return jsonify(dict(code=404, message="Not Found")), 404

    @app.errorhandler(500)
    def page_500(error):
        return jsonify(dict(code=500, message="Internal Server Error")), 500


def register_hooks(app):
    """Register hooks."""

    @app.before_request
    def before_request():
       g.user = get_current_user()
       if g.user is not None and g.user.has_role('admin'):
           g._before_request_time = time.time()

    @app.after_request
    def after_request(response):
        if hasattr(g, '_before_request_time'):
            delta = time.time() - g._before_request_time
            response.headers['X-Render-Time'] = delta * 1000
        return response


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
