# encoding: utf-8

import datetime
from ._base import db


'''
Describe model here!!!
'''
class WorkFlow(db.Model):
    # Fields
    id =  db.Column(db.Integer, primary_key = True)
    name =  db.Column(db.String(255), index = True)
    active =  db.Column(db.Integer, default = True)
    created_at =  db.Column(db.DateTime, default = datetime.datetime.now)
    updated_at =  db.Column(db.DateTime, default = datetime.datetime.now, onupdate = datetime.datetime.now)

    def __repr__(self):
        return '<WorkFlow name = %s, created_at = %s>' %(self.name, self.created_at)
