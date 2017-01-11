import logging
from flask import url_for, request, session, redirect, flash
from flask_security import current_user
from flask_security.utils import login_user, logout_user
from flask_oauthlib.client import OAuth, OAuthException
from application.models import db, User


def init_social_auth(app):
    if not app.config.get('FACEBOOK_APP_ID', None) and not \
           app.config.get("FACEBOOK_APP_SECRET", None):

        logging.warning('Social Authentiation module not found config.')
        logging.warning('example. FACEBOOK_APP_ID and FACEBOOK_APP_SECRET')
        return False

    oauth = OAuth()
    facebook = oauth.remote_app('facebook',
            consumer_key=app.config.get('FACEBOOK_APP_ID'),
            consumer_secret=app.config.get('FACEBOOK_APP_SECRET'),
            request_token_params=dict(scope='email'),
            request_token_url=None,
            access_token_url='/oauth/access_token',
            access_token_method='GET',
            authorize_url='https://www.facebook.com/dialog/oauth',
            base_url='https://graph.facebook.com')


    @app.route("/social_login/<string:provider>")
    def social_login(provider):
        if provider == 'facebook':
            callback = url_for('facebook_authorized',
                    next=request.args.get('next')
                        or request.referrer
                        or None,
                    _external=True)
            return facebook.authorize(callback=callback)
        raise 'Provider %s not found' % provider


    @app.route('/social_login/fb_authorized')
    def facebook_authorized():
        resp = facebook.authorized_response()
        if resp is None:
            return 'Access denied: reason=%s error=%s' % (
                    request.args['error_reason'],
                    request.args['error_description']
                    )

        if isinstance(resp, OAuthException):
            return 'Access denied: %s' % resp.message

        session['access_token'] = (resp['access_token'], '')
        me = facebook.get('/me/?fields=email,name,id,picture.height(200).width(200)')
        return set_user('Facebook', me)


    @facebook.tokengetter
    def get_facebook_access_token():
        return session.get('access_token')


    def set_user(provider, me):
        user = User.query.filter_by(auth_provider_id=provider, 
                                    auth_provider_user_id=me.data['id']).first()
        if user is None:
            user = create_user(me, provider)
            return redirect(url_for('site.index'))

        signin_user(user, remember=True)
        return redirect(url_for('site.index'))

    
    def create_user(me, provider):
        if provider == 'Facebook':
            profile_url = me.data['picture']['data']['url']
        else:
            profile_url = me.data['picture']

        new_user = User(auth_provider_id=provider,
                auth_provider_user_id=me.data['id'],
                name=me.data['name'],
                auth_provider_profile_pic=profile_url)
        
        db.session.add(new_user)
        db.session.commit()
        signin_user(new_user, remember=True)
        return new_user


def get_current_user():
    if 'user_id' in session:
        user = User.query.get(int(session["user_id"]))
        return user
    return current_user


def signin_user(user, remember=True):
    login_user(user, remember)
    session['user_id'] = user.id


def signout_user():
    session.pop("user_id", None)
