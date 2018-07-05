from .suite import BaseSuite
from application.models.work_flow import WorkFlow
from application.utils.workflow import init_new_flow
from application.utils.workflow import proceed_flow
from application.utils.workflow import _save_yml_to_db
from application.utils.workflow import proceed_flow_decorator
from application.utils.workflow import proceed_flow_decorator_from_state
from application.models import db
from application.models.work_flow import WorkFlow
from application.models.work_flow_state import WorkFlowState
from application.models.work_flow_transition import WorkFlowTransition
from application.models.work_flow_instance import WorkFlowInstance
from application.models.work_flow_instance_detail import WorkFlowInstanceDetail
import yaml

#from application.models.simple_object import SimpleObject
class SimpleObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    def __repr__(self):
        return '<SimpleObject name = %s>' %self.name

Example = """
Example:
    states:
        -   name: state0
            model: SimpleObject
            is_initial_state: true

        -   name: state1
            model: SimpleObject

        -   name: state2
            model: SimpleObject

        -   name: state3
            model: SimpleObject

        -   name: state4
            model: SimpleObject

        -   name: state5
            model: SimpleObject

        -   name: state6
            model: SimpleObject

        -   name: state7
            model: SimpleObject
            is_success_state: true

    transitions:
        0_to_1:
            from_state: state0
            to_state: state1
            type: sequence
            condition: "name='state0 complete'"
            callable_condition: func_0_1()

        1_choice_2_3:
            from_state: state1
            to_state: [state2, state3]
            type: choice
            condition:
                state2: "name='choose 2'"
                state3: "name='choose 3'"

        2_3_merge_4:
            from_state: [state2, state3]
            to_state: state4
            type: merge
            condition:
                state2: "name='job 2 done'"
                state3: "name='job 3 done'"

        4_split_5_6:
            from_state: state4
            to_state: [state5, state6]
            type: split
            condition: "name='state 4 done'"

        5_6_synch_7:
            from_state: [state5, state6]
            to_state: state7
            type: synch
            condition:
                state5: "name='job 5 done'"
                state6: "name='job 6 done'"
"""

class TestYmlWorkFlow(BaseSuite):
    def test_load_and_run_yml_work_flow(self):
        with self.app.app_context():
            print()
            yml = yaml.load(Example)
            db.session.commit()

            # Load flow from YML
            assert _save_yml_to_db(yml) == True
            db.session.commit()

            wf = WorkFlow.query.first()
            assert wf.name == 'Example'
            assert len(wf.states) == 8
            assert len(wf.transitions) == 9
            tokens = set([t.transition_token for t in wf.transitions])
            assert len(tokens) == 5 # For choice, they aren't grouped transition together. really?
            
            # Make new instance of work flow
            o = SimpleObject(name='init')
            db.session.commit()

            wfi = init_new_flow(wf, 'master_instance', {'state0': o})
            db.session.commit()

            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state0"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 0 -> state 1, sequenece
            o.name = 'state0 complete'
            db.session.commit()

            r = proceed_flow(wfi)
            db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state1"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 1 -> state 3, exclusive choice (another way is state 1 -> state 2)
            o.name = 'choose 3'
            db.session.commit()

            r = proceed_flow(wfi)
            db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state3"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 3 -> state 4, simple merge (another way is state 2 -> state 4)
            o.name = 'job 3 done'
            db.session.commit()

            r = proceed_flow(wfi)
            db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state4"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 4 -> state 5 and 6, split
            o5 = SimpleObject(name='for state5')
            o6 = SimpleObject(name='for state6')
            o.name = 'state 4 done'
            db.session.commit()

            r = proceed_flow(wfi, {'state5': o5, 'state6': o6})
            db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 2
            for i in wfi.current_details:
                assert i.ref_object.name.find(i.work_flow_state.name) >= 0
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 5 and 6 -> state 7, synch
            o7 = SimpleObject(name='final state')
            o5.name = 'job 5 done'
            o6.name = 'job 6 done'
            db.session.commit()

            r = proceed_flow(wfi, {'state7': o7})
            db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o7
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state7"
            assert wfi.is_success == True
            assert wfi.is_failed == False

    def test_load_and_run_yml_work_flow_decorate(self):
        with self.app.app_context():
            print()
            yml = yaml.load(Example)
            db.session.commit()

            # Load flow from YML
            assert _save_yml_to_db(yml) == True
            db.session.commit()

            wf = WorkFlow.query.first()
            assert wf.name == 'Example'
            assert len(wf.states) == 8
            assert len(wf.transitions) == 9
            tokens = set([t.transition_token for t in wf.transitions])
            assert len(tokens) == 5 # For choice, they aren't grouped transition together. really?

            # Make new instance of work flow
            o = SimpleObject(name='init')
            db.session.commit()

            wfi = init_new_flow(wf, 'master_instance', {'state0': o})
            db.session.commit()

            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state0"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 0 -> state 1, sequenece
            o.name = "don't care"
            db.session.commit()

            @proceed_flow_decorator
            def sequence_state_0_to_1(workflow_instance=None, object_by_next_state={}):
                return True

            r = sequence_state_0_to_1(workflow_instance=wfi, object_by_next_state={'state1': o})
            db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state1"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 1 -> state 2, exclusive choice (another way is state 1 -> state 3)
            o.name = "still don't care"
            db.session.commit()

            @proceed_flow_decorator
            def choice_state_1_to_2_or_3(workflow_instance, object_by_next_state):
                return "state2"

            r = choice_state_1_to_2_or_3(workflow_instance=wfi, object_by_next_state={'state2': o, 'state3': o})
            db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state2"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 2 -> state 4, simple merge (another way is state 3 -> state 4)
            o.name = "don't care again"
            db.session.commit()

            @proceed_flow_decorator
            def merge_state_2_3_to_4(workflow_instance, object_by_next_state):
                return True

            r = merge_state_2_3_to_4(workflow_instance=wfi, object_by_next_state={'state4': o})
            db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state4"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 4 -> state 5 and 6, split
            o5 = SimpleObject(name='for state5')
            o6 = SimpleObject(name='for state6')
            o.name = "who care"
            db.session.commit()

            @proceed_flow_decorator
            def split_state_4_to_5_6(workflow_instance, object_by_next_state):
                return True

            r = split_state_4_to_5_6(workflow_instance=wfi, object_by_next_state={'state5': o5, 'state6': o6})
            db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 2
            for i in wfi.current_details:
                assert i.ref_object.name.find(i.work_flow_state.name) >= 0
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 5 and 6 -> state 7, synch
            o7 = SimpleObject(name='final state')
            o5.name = 'job 5 done, you care?'
            o6.name = 'job 6 done. what!!!'
            db.session.commit()

            @proceed_flow_decorator
            def synch_state_5_6_to_7(workflow_instance, object_by_next_state):
                return True

            #r = synch_state_5_6_to_7(workflow_instance=wfi, object_by_next_state={'state7': o7})
            r = sequence_state_0_to_1(workflow_instance=wfi, object_by_next_state={'state7': o7})
            db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o7
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state7"
            assert wfi.is_success == True
            assert wfi.is_failed == False

    def test_load_and_run_yml_work_flow_decorate_with_state(self):
        with self.app.app_context():
            print()
            yml = yaml.load(Example)
            db.session.commit()

            # Load flow from YML
            assert _save_yml_to_db(yml) == True
            db.session.commit()

            wf = WorkFlow.query.first()
            assert wf.name == 'Example'
            assert len(wf.states) == 8
            assert len(wf.transitions) == 9
            tokens = set([t.transition_token for t in wf.transitions])
            assert len(tokens) == 5 # For choice, they aren't grouped transition together. really?

            # Make new instance of work flow
            o = SimpleObject(name='init')
            db.session.commit()

            wfi = init_new_flow(wf, 'master_instance', {'state0': o})
            db.session.commit()

            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state0"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 0 -> state 1, sequenece
            o.name = "don't care"
            db.session.commit()

            @proceed_flow_decorator_from_state(['state0'])
            def sequence_state_0_to_1(workflow_instance=None, object_by_next_state={}):
                # You can return either True or a state name
                #return True
                return 'state1'

            r = sequence_state_0_to_1(workflow_instance=wfi, object_by_next_state={'state1': o})
            if r: db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state1"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 1 -> state 2, exclusive choice (another way is state 1 -> state 3)
            o.name = "still don't care"
            db.session.commit()

            @proceed_flow_decorator_from_state(['state1'])
            def choice_state_1_to_2_or_3(workflow_instance, object_by_next_state):
                # You can return only a state name
                return "state2"

            r = choice_state_1_to_2_or_3(workflow_instance=wfi, object_by_next_state={'state2': o, 'state3': o})
            if r: db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state2"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 2 -> state 4, simple merge (another way is state 3 -> state 4)
            o.name = "don't care again"
            db.session.commit()

            @proceed_flow_decorator_from_state(['state2'])
            def merge_state_2_3_to_4(workflow_instance, object_by_next_state):
                # You can return either True or a state name
                #return True
                return 'state4'

            r = merge_state_2_3_to_4(workflow_instance=wfi, object_by_next_state={'state4': o})
            if r: db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state4"
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 4 -> state 5 and 6, split
            o5 = SimpleObject(name='for state5')
            o6 = SimpleObject(name='for state6')
            o.name = "who care"
            db.session.commit()

            @proceed_flow_decorator_from_state(['state4'])
            def split_state_4_to_5_6(workflow_instance, object_by_next_state):
                # You can return either True or a list of state names
                #return True
                return ['state5', 'state6']

            r = split_state_4_to_5_6(workflow_instance=wfi, object_by_next_state={'state5': o5, 'state6': o6})
            if r: db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 2
            for i in wfi.current_details:
                assert i.ref_object.name.find(i.work_flow_state.name) >= 0
            assert wfi.is_success == False
            assert wfi.is_failed == False

            # Proceed flow: state 5 and 6 -> state 7, synch
            o7 = SimpleObject(name='final state')
            o5.name = 'job 5 done, you care?'
            o6.name = 'job 6 done. what!!!'
            db.session.commit()

            @proceed_flow_decorator_from_state(['state5', 'state6'])
            def synch_state_5_6_to_7(workflow_instance, object_by_next_state):
                # You can return either True or a state name
                #return True
                return 'state7'

            r = synch_state_5_6_to_7(workflow_instance=wfi, object_by_next_state={'state7': o7})
            if r: db.session.commit()

            assert r == True
            assert len(wfi.current_details) == 1
            assert wfi.current_details[0].ref_object == o7
            assert wfi.current_details[0].is_current_state == True
            assert wfi.current_details[0].work_flow_state.name == "state7"
            assert wfi.is_success == True
            assert wfi.is_failed == False
