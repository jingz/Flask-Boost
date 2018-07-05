from .suite import BaseSuite
from application.models.work_flow import WorkFlow
from application.models import db

class TestWorkFlowController(BaseSuite):
    def test_create(self):
        with self.app.app_context():
            d = dict(
                data = dict(
                    name='test',
                    active=True,
                )
            )
            rv = self.client.post("/work_flow/", json=d)
            assert rv.status_code == 201
            data = rv.json
            assert WorkFlow.query.count() == 1


    def test_list(self):
        with self.app.app_context():
            wf = WorkFlow(name='test', active=True)
            db.session.add(wf)
            db.session.commit()

            rv = self.client.get("/work_flow/")
            assert rv.status_code == 200
            data = rv.json
            assert data['count'] == 1


    def test_show(self):
        with self.app.app_context():
            wf = WorkFlow(name='test', active=True)
            db.session.add(wf)
            db.session.commit()

            rv = self.client.get("/work_flow/%d" %wf.id)
            assert rv.status_code == 200
            data = rv.json
            assert data['data']['name'] == 'test'


    def test_update(self):
        with self.app.app_context():
            wf = WorkFlow(name='test_update', active=True)
            db.session.add(wf)
            db.session.commit()

            d = dict(
                data = dict(
                    name='test test',
                    active=True,
                )
            )
            rv = self.client.put("/work_flow/%d" %wf.id, json=d)
            assert rv.status_code == 200
            data = rv.json
            assert WorkFlow.query.first().name == "test test"


    def test_delete(self):
        with self.app.app_context():
            wf = WorkFlow(name='test', active=True)
            db.session.add(wf)
            db.session.commit()

            rv = self.client.delete("/work_flow/%d" %wf.id)
            assert rv.status_code == 200
            data = rv.json
            assert data['success'] == True
            assert WorkFlow.query.count() == 0
