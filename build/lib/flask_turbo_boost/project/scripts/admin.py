from flask import current_app
from flask_security import SQLAlchemyUserDatastore
from flask_script import Command, Manager, Option
from application.models import db
import application.models as models

admin_manager = Manager(current_app, help="Manage admin stuff such as creating user.")

@admin_manager.option("--name", "-n", dest="name", default='admin')
def create_fs_admin(name='admin'):
    """ create initial flask security admin """

    # find role admin
    r = models.Role.query.filter_by(name='admin').first()
    if not r:
        r = models.Role(name='admin', description='admin role')
        try:
            db.session.add(r)
            db.session.commit()
        except:
            print("cannot create role")

    u = models.User.query.filter_by(name=name).first()
    if not u:
        user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
        email = "%s@email.com" % name
        user_datastore.create_user(email=email, 
                name='admin',
                is_admin=True,
                password='password',
                roles=['admin'])
        try:
            db.session.commit()
            print("admin name: %s was created!" % name)
        except Exception as e:
            print(e.message)
    else:
        print("admin name: %s already existed" % name)
