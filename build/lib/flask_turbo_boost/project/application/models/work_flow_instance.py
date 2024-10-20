# encoding: utf-8

import datetime
from ._base import db


'''
Describe model here!!!
'''
class WorkFlowInstance(db.Model):
    # Fields
    id =  db.Column(db.Integer, primary_key = True)

    name = db.Column(db.String(255), index=True)

    work_flow_id =  db.Column(db.Integer, db.ForeignKey('work_flow.id'))
    work_flow = db.relationship('WorkFlow', backref = 'instances')

    current_details = db.relation("WorkFlowInstanceDetail",
        primaryjoin="and_(WorkFlowInstance.id==WorkFlowInstanceDetail.work_flow_instance_id, "
                         "WorkFlowInstanceDetail.active==True, "
                         "WorkFlowInstanceDetail.is_current_state==True)",
        uselist=True)

    is_success =  db.Column(db.Boolean, default = False)
    is_failed =  db.Column(db.Boolean, default = False)
    active =  db.Column(db.Integer, default = True)
    created_at =  db.Column(db.DateTime, default = datetime.datetime.now)
    updated_at =  db.Column(db.DateTime, default = datetime.datetime.now, onupdate = datetime.datetime.now)

    def __repr__(self):
        return '<WorkFlowInstance name=%s, created_at = %s>' %(self.name, self.created_at,)
