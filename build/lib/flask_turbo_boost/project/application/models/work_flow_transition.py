# encoding: utf-8

import datetime
from ._base import db


'''
Describe model here!!!
'''
class WorkFlowTransition(db.Model):
    # Fields
    id =  db.Column(db.Integer, primary_key = True)

    work_flow_id =  db.Column(db.Integer, db.ForeignKey('work_flow.id'))
    work_flow = db.relationship('WorkFlow', backref = 'transitions')

    name = db.Column(db.String(255), index = True)

    from_state_id =  db.Column(db.Integer, db.ForeignKey('work_flow_state.id'))

    to_state_id =  db.Column(db.Integer, db.ForeignKey('work_flow_state.id'))

    # Can be sequence, split, synch, choice, merge
    transition_type =  db.Column(db.String(64), default = 'sequence')

    # When there are multiple transitions, 
    transition_token = db.Column(db.String(128))

    # Transition condition
    transition_condition = db.Column(db.String(512))

    active =  db.Column(db.Integer, default = True)
    created_at =  db.Column(db.DateTime, default = datetime.datetime.now)
    updated_at =  db.Column(db.DateTime, default = datetime.datetime.now, onupdate = datetime.datetime.now)

    def __repr__(self):
        return '<WorkFlowTransition from_state = %s, to_state = %s, created_at = %s>' %(self.from_state_id, self.to_state_id, self.created_at)
