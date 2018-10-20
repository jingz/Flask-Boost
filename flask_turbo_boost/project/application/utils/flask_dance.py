from flask import flash
from application.models import db, OAuth, User
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask_dance.consumer.backend.sqla import SQLAlchemyBackend
from flask_dance.consumer import oauth_authorized
from flask_security import login_user, current_user


def init_flask_dance(app):
    fb_blueprint = make_facebook_blueprint(
        client_id=app.config.get("FACEBOOK_CLIENT_ID"),
        client_secret=app.config.get("FACEBOOK_CLIENT_SECRET"),
        scope='email',
        backend=SQLAlchemyBackend(OAuth, session=db.session)
    )

    @oauth_authorized.connect_via(fb_blueprint)
    def facebook_logged_in(bp, token):
        if not token:
           flash('Fail to login with facebook')
           return False

        resp = facebook.get('/me?fields=email,name,picture')
        if resp.status_code != 200:
            flash('Fail to get user profile form facebook')
            return False


        '''
            # response
        {
            'email': 'user@email.com',
            'name': 'Firstname Lastname',
            'picture': {'data': {'height': 50,
                        'is_silhouette': False,
                        'url': 'https://image_url',
                        'width': 50}},
            'id': '128371982371892'
        }
        '''
        user_info = resp.json()
        email = user_info.get('email')
        if not email:
            flash('Fail to search user with no email')
            return False

        # check oauth record
        auth = OAuth.query.filter_by(provider=fb_blueprint.name,
                                     provider_user_id=user_info['id']).first()

        # create auth if not existing
        if not auth:
            auth = OAuth(provider=fb_blueprint.name,
                        provider_user_id=user_info['id'],
                        token=token)
                    
            db.session.add(auth)

        # check associated user
        if not auth.user:
            auth.user = User(email=user_info['email'],
                        name=user_info['name'])

            try:
                image_url = user_info.get('picture').get('data').get('url')
                auth.user.avatar = image_url
            except Exeption as e:
                pass

        db.session.commit()
        db.session.refresh(auth.user)
        login_user(auth.user)

        # prevent flask-dance trigger twice
        return False

    
    # register to the app
    app.register_blueprint(fb_blueprint, url_prefix="/fb_login")
