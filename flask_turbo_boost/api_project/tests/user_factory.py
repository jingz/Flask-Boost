import factory
from application.models import db, User, Role
from .role_factory import RoleFactory
from werkzeug.security import generate_password_hash, check_password_hash

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

    name = factory.Faker("first_name")
    # name = factory.Faker('name')
    password ="123123"
    email = factory.Faker('email')
    active = True


class AdminUserFactory(UserFactory):
    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        r = Role.find(name='admin')
        if not r:
            r = RoleFactory(name='admin')
        self.roles.append(r)
        db.session.commit()


class EditorUserFactory(UserFactory):
    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        r = Role.find(name='editor')
        if not r:
            r = RoleFactory(name='editor')
        self.roles.append(r)
        db.session.commit()


class ApproverUserFactory(UserFactory):
    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        r = Role.find(name='approver')
        if not r:
            r = RoleFactory(name='approver')
        self.roles.append(r)
        db.session.commit()
