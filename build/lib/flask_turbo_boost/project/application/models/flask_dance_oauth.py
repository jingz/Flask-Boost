# coding: utf-8
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from ._base import db


class OAuth(db.Model, OAuthConsumerMixin):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    provider_user_id = db.Column(db.String(200))
    user = db.relationship("User")

    def __repr__(self):
        return '<OAuth provider %s, %s>' % (self.provider, self.provider_user_id)
