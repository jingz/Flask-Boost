# encoding: utf-8

import datetime
from ._base import db
from sqlalchemy_utils import generic_relationship


'''
Describe model here!!!
'''
class WorkFlowInstanceDetail(db.Model):
    # Fields
    id =  db.Column(db.Integer, primary_key = True)

    work_flow_instance_id =  db.Column(db.Integer, db.ForeignKey('work_flow_instance.id'))
    work_flow_instance = db.relationship('WorkFlowInstance', backref = 'details')

    work_flow_state_id =  db.Column(db.Integer, db.ForeignKey('work_flow_state.id'))
    work_flow_state = db.relationship('WorkFlowState', backref = 'instances')

    # Build generic relationship to target model object
    ref_model   =  db.Column(db.String(255))
    ref_id      =  db.Column(db.Integer)
    ref_object  =  generic_relationship(ref_model, ref_id)

    is_current_state = db.Column(db.Boolean, default=False)

    active =  db.Column(db.Integer, default = True)
    created_at =  db.Column(db.DateTime, default = datetime.datetime.now)
    updated_at =  db.Column(db.DateTime, default = datetime.datetime.now, onupdate = datetime.datetime.now)

    def __repr__(self):
        return '<WorkFlowInstance id = %s, ref_model = %s, ref_id = %s>' %(self.id, self.ref_model, self.ref_id)
