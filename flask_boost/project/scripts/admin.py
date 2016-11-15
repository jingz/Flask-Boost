from flask import current_app
from flask_script import Command, Manager, Option
from application.models import db
import application.models as models

admin_manager = Manager(current_app, help="Manage admin stuff such as creating user.")

@admin_manager.option("--name", "-n", dest="name", default='admin')
def create_admin(name='admin'):
    # find role admin
    r = models.Role.query.filter_by(name='admin').first()
    if not r:
        r = models.Role(name='admin', description='admin role')
        try:
            db.session.add(r)
            db.session.commit()
        except:
            print "cannot create role"

    u = models.User.query.filter_by(name=name).first()
    if not u:
        u = models.User(name=name)
        u.email = "%s@email.com" % name
        u.password = "password"
        u.is_admin = True
        u.active = True
        try:
            u.roles.append(r)
            db.session.add(u)
            db.session.commit()
        except Exception, e:
            print e.message
    else:
        print "admin name: %s was created!" % name
