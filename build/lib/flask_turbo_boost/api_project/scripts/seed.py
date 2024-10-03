import click
from flask.cli import AppGroup, with_appcontext
from application.models import User

seed_cli = AppGroup('seed')

@seed_cli.command('admin')  # flask seed users
@with_appcontext
def seed_admin():
    print("seed users")
    print("number of users is %s" % User.query.count())
