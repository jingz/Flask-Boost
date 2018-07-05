# encoding: utf-8

import datetime
from ._base import db


'''
Describe model here!!!
'''
class WorkFlowState(db.Model):
    # Fields
    id =  db.Column(db.Integer, primary_key = True)

    work_flow_id =  db.Column(db.Integer, db.ForeignKey('work_flow.id'))
    work_flow = db.relationship('WorkFlow', backref = 'states')

    name =  db.Column(db.String(255), index = True)
    model =  db.Column(db.String(255))

    is_initial_state =  db.Column(db.Boolean, default = False)
    is_success_state =  db.Column(db.Boolean, default = False)
    is_failed_state =  db.Column(db.Boolean, default = False)

    out_transitions = db.relationship("WorkFlowTransition",
        primaryjoin="and_(WorkFlowState.id==WorkFlowTransition.from_state_id, "
                         "WorkFlowTransition.active==True)",
        backref='from_state',
        uselist=True)

    in_transitions = db.relationship("WorkFlowTransition",
        primaryjoin="and_(WorkFlowState.id==WorkFlowTransition.to_state_id, "
                         "WorkFlowTransition.active==True)",
        backref='to_state',
        uselist=True)

    active =  db.Column(db.Integer, default = True)
    created_at =  db.Column(db.DateTime, default = datetime.datetime.now)
    updated_at =  db.Column(db.DateTime, default = datetime.datetime.now, onupdate = datetime.datetime.now)

    def __repr__(self):
        return '<WorkFlowState name = %s, created_at = %s>' %(self.name, self.created_at)
