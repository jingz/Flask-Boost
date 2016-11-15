# coding: utf-8
import os
import glob2
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from application import create_app
from application.models import db
import application.models as models
from scripts.admin import admin_manager
from scripts.form import form_manager

# Used by app debug & livereload
PORT = 5000

app = create_app()
manager = Manager(app)

# db migrate commands
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
manager.add_command('admin', admin_manager)
manager.add_command('form', form_manager)

def _make_shell_context():
    return dict(app=app, db=db, m=models)

manager.add_command('shell', Shell(make_context=_make_shell_context))


@manager.command
def run():
    """Run app."""
    app.run(port=PORT)


@manager.command
def live():
    """Run livereload server"""
    from livereload import Server

    server = Server(app)

    map(server.watch, glob2.glob("application/pages/**/*.*"))  # pages
    map(server.watch, glob2.glob("application/macros/**/*.html"))  # macros
    map(server.watch, glob2.glob("application/static/**/*.*"))  # public assets

    server.serve(port=PORT)


@manager.command
def build():
    """Use FIS to compile assets."""
    os.system('gulp')
    os.chdir('application')
    os.system('fis release -d ../output -opmD')


if __name__ == "__main__":
    manager.run()
