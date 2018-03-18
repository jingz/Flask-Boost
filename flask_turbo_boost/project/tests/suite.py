# coding: utf-8
import os
from application import create_app
from application.models import db


def create_test_app():
    os.environ['MODE'] = 'TESTING'
    app = create_app()
    return app


class BaseSuite(object):
    def setup(self):
        app = create_test_app()
        self.app = app
        self.client = app.test_client()

        with app.app_context():
            db.drop_all()
            db.create_all()

    def teardown(self):
        with self.app.app_context():
            db.drop_all()
