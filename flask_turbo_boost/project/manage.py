# coding: utf-8
import os
import glob2
from flask import url_for
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from application import create_app
from application.models import db
import application.models as models
from scripts.admin import admin_manager
from scripts.form import form_manager
from scripts.scaffold import scaffold_manager

# Used by app debug & livereload
PORT = 5000

app = create_app()
manager = Manager(app)

# db migrate commands
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
manager.add_command('admin', admin_manager)
manager.add_command('form', form_manager)
manager.add_command('scaffold', scaffold_manager)

def _make_shell_context():
    return dict(app=app, db=db, m=models)

manager.add_command('shell', Shell(make_context=_make_shell_context))


@manager.command
def run():
    """Run app."""
    app.run(port=PORT)


@manager.command
def init_psa():
    from application.models import db
    from social.apps.flask_app.default import models
    models.PSABase.metadata.create_all(db.engine)


if __name__ == "__main__":
    manager.run()
