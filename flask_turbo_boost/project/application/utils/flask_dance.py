from flask import flash, current_app
from flask_security import login_user, current_user
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from application.models import db, OAuth, User


def init_flask_dance(app):
    facebook_bp = create_facebook_bluprint(app)
    google_bp = create_google_blueprint()

    # register auth blueprints to the app
    app.register_blueprint(facebook_bp)
    app.register_blueprint(google_bp)


def create_facebook_bluprint(app):
    """
    Create facebook auth blueprint with default config variables client id and
    secret

    https://flask-dance.readthedocs.io/en/latest/providers.html#module-flask_dance.contrib.facebook

    Default authorized redirect uri: /facebook/authorized
    (use to register in facebook login setting )

    """

    fb_blueprint = make_facebook_blueprint(scope='email')

    @oauth_authorized.connect_via(fb_blueprint)
    def facebook_logged_in(bp, token):
        if not token:
            flash('Fail to login with facebook')
            return False

        resp = facebook.get('/me?fields=email,name,picture')
        if not resp.ok:
            flash('Fail to get user profile form facebook', category="error")
            return False

        # example response
        '''
        {
            'email': 'user@email.com',

            'picture': {'data': {'height': 50,
                        'is_silhouette': False,
                        'url': 'https://image_url',
                        'width': 50}},
            'id': '128371982371892'
        }
        '''

        user_info = resp.json()
        picture = None
        try:
            picture = user_info.get('picture').get('data').get('url')
        except:
            pass

        try:
            ok = _save_and_login_user(user_id=user_info.get('id'),
                                      user_name=user_info.get('name'),
                                      email=user_info.get('email'),
                                      picture=picture,
                                      token=token,
                                      provider_name=fb_blueprint.name)
            if ok:
                flash("Successfully signed in with Facebook.")

        except Exception as e:
            current_app.logger.error(
                "[Flask Dance: facebook] cannot save and login user %s" %
                str(e))
            db.session.rollback()

        # prevent flask-dance trigger twice
        return False

    return fb_blueprint


def create_google_blueprint():
    """
    Google use default config variables
    GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET
    https://developers.google.com/identity/protocols/oauth2/scopes#google-sign-in
    https://flask-dance.readthedocs.io/en/latest/providers.html#module-flask_dance.contrib.facebook
    Default redirect uri: /google/authorized
    """

    g_blueprint = make_google_blueprint(scope=[
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile', 'openid'
    ])

    @oauth_authorized.connect_via(g_blueprint)
    def google_logged_in(bp, token):
        if not token:
            flash('Fail to login with facebook')
            return False

        # resp = facebook.get('/me?fields=email,name,picture')
        resp = google.get("/oauth2/v2/userinfo")
        if resp.status_code != 200:
            flash('Fail to get user profile form facebook', category='error')
            return False
        """ example response
            {
              "id": "2942903842893",
              "email": "youmail@gmail.com"
              "name": "Firstname Lastname",
              "given_name": "firstname",
              "family_name": "lastname",
              "link": "https://plus.google.com/3247298347928734",
              "picture": "https://lh6.googleusercontent.com/asdkfjskfjsdkjf",
              "gender": "male",
              "locale": "en"
            }

        """
        user_info = resp.json()

        try:
            ok = _save_and_login_user(user_id=user_info.get('id'),
                                      user_name=user_info.get('name'),
                                      email=user_info.get('email'),
                                      picture=user_info.get('picture'),
                                      token=token,
                                      provider_name=g_blueprint.name)
            if ok:
                flash("Successfully signed in with Google.")
        except Exception as e:
            current_app.logger.error(
                "[Flask Dance: Google] cannot save and login user %s" % str(e))
            db.session.rollback()

        return False

    return g_blueprint


def _save_and_login_user(user_id=None,
                         user_name=None,
                         email=None,
                         picture=None,
                         token=None,
                         provider_name=None):
    if not email:
        flash('Fail to search user with no email', category='error')
        return False

    # check oauth record
    auth = OAuth.query.filter_by(provider=provider_name,
                                 provider_user_id=user_id).first()

    current_app.logger.debug(auth)
    # create auth if not existing
    if not auth:
        auth = OAuth(provider=provider_name,
                     provider_user_id=user_id,
                     token=token)

        db.session.add(auth)

    # check associated user
    # if not auth.user:
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, name=user_name, active=True)

    auth.user = user
    if picture:
        auth.user.avatar = picture

    db.session.commit()
    db.session.refresh(user)
    login_user(user)
    return True
