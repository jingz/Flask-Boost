import sys, os
path = os.path.abspath(os.path.join(os.path.split(os.path.abspath(__file__))[0], '..', '..'))
if sys.path.count(path) == 0: sys.path.insert(0, path)

import yaml
import itertools
from sqlalchemy import text
from application.models import db
from application.models.work_flow import WorkFlow
from application.models.work_flow_transition import WorkFlowTransition
from application.models.work_flow_state import WorkFlowState
from application.models.work_flow_instance import WorkFlowInstance
from application.models.work_flow_instance_detail import WorkFlowInstanceDetail

# Exceptions
class WorkFlowException(Exception):
    def to_dict(self):
        return dict(message=self.message)

class InitModelInstanceException(WorkFlowException):
    pass

class NotUniqueTransitionTypeException(WorkFlowException):
    pass

class SequenceTypeException(WorkFlowException):
    pass

class SplitTypeException(WorkFlowException):
    pass

class SynchTypeException(WorkFlowException):
    pass

class ChoiceTypeException(WorkFlowException):
    pass

class MergeTypeException(WorkFlowException):
    pass

# Constants
class TransitionType(object):
    Sequence    = 'sequence'
    Split       = 'split'  # parallel split
    Synch       = 'synch'  # synchronization
    Choice      = 'choice' # exclusive choice
    Merge       = 'merge'  # simple merge

# Build flow
def create_workflow(name):
    if WorkFlow.query.filter_by(name=name,active=True).count() > 0:
        raise WorkFlowException("Duplicate workflow template name")
    wf = WorkFlow(name=name, active=True)
    db.session.add(wf)
    return wf

def add_workflow_state(workflow, state_name, model, initial_state=False, success_state=False, fail_state=False):
    wfs = WorkFlowState(
        work_flow=workflow,
        name=state_name,
        model=model,
        active=True,
        is_initial_state=initial_state,
        is_success_state=success_state,
        is_failed_state=fail_state
    )
    db.session.add(wfs)
    return wfs

def add_workflow_transition(workflow, name, from_state=None, to_state=None, transition_type=TransitionType.Sequence, transition_condition=None, transition_token=None):
    wft = WorkFlowTransition(
        work_flow = workflow,
        name = name,
        from_state = from_state,
        to_state = to_state,
        transition_type = transition_type,
        transition_condition = transition_condition,
        transition_token = transition_token,
        active = True,
    )
    db.session.add(wft)
    return wft

def _sequence(master_flow_instance,
              instance_by_transition,
              transitions,
              object_by_next_state={},
              condition_function=None,
              args=[],
              kwargs={}):
    transition = transitions[0]
    from_flow_instance  = instance_by_transition[transition]

    cond = transition.transition_condition.strip()
    proceed = False
    obj = from_flow_instance.ref_object
    if cond:
        # Test condition if flow can proceed or not
        if condition_function:
            proceed = condition_function(*args, **kwargs)
        else:
            model = obj.__class__
            if model.query.filter_by(id=obj.id).filter(text(cond)).count() > 0:
                proceed = True
    else:
        proceed = True

    if not proceed: return False

    next_state = transition.to_state
    if proceed is not True and\
       next_state.name != proceed:
        return False

    # If no next state object, use the same object from previous current state
    next_state_object = object_by_next_state.get(next_state.name)
    if next_state_object is None: next_state_object = obj

    # Create new flow instance detail as current state instance, which refer to next_state_object
    if next_state_object.id is None:
        db.session.add(next_state_object)
        db.session.flush()

    wfid = WorkFlowInstanceDetail(
        work_flow_instance = master_flow_instance,
        work_flow_state = next_state,
        ref_object = next_state_object,
        is_current_state = True,
        active = True,
    )
    db.session.add(wfid)

    # This state is not current state anymore
    from_flow_instance.is_current_state = False

    # Check if flow is success of fail
    if next_state.is_success_state:
        master_flow_instance.is_success = True
    if next_state.is_failed_state:
        master_flow_instance.is_failed = True

    # Proceed to next state success
    return True


def _split(master_flow_instance,
           instance_by_transition,
           transitions,
           object_by_next_state={},
           condition_function=None,
           args=[],
           kwargs={}):
    s = set([instance_by_transition[t] for t in transitions]) # All of transitions must have the same detail_instance
    if len(s) != 1:
        raise SplitTypeException("With split flow type, you must have only one source state")
    from_flow_instance  = s.pop()

    conds = set([t.transition_condition.strip() for t in transitions])
    next_state_ids = list(set([t.to_state_id for t in transitions]))

    next_states = WorkFlowState.query.filter(WorkFlowState.id.in_(next_state_ids)).all()
    state_by_id = dict([(s.id, s) for s in next_states ])

    # Check if we can proceed all split branch (actually, it should be used the same condition for split)
    obj = from_flow_instance.ref_object
    proceed = True
    if condition_function:
        proceed = condition_function(*args, **kwargs)
    else:
        for cond in conds:
            model = obj.__class__
            if model.query.filter_by(id=obj.id).filter(text(cond)).count() == 0:
                proceed = False

    # If we can't proceed, just return False
    if not proceed: return False
    if proceed is not True:
        if type(proceed) is not list: return False
        next_state_names = set([st.name for st in next_states])
        if set(proceed) != next_state_names: return False

    # Create all next state instance with ref object
    success = False
    failed = False
    wfids = []
    for t in transitions:
        next_state = state_by_id[t.to_state_id]
        next_obj   = object_by_next_state.get(next_state.name)
        if not next_obj:
            next_obj = obj  # Re-use old objects

        if next_obj.id is None:
            db.session.add(next_obj)
            db.session.flush()

        wfid = WorkFlowInstanceDetail(
            work_flow_instance = master_flow_instance,
            work_flow_state = next_state,
            ref_object = next_obj,
            is_current_state = True,
            active = True,
        )
        wfids.append(wfid)

        if next_state.is_success_state:
            success = True
        if next_state.is_failed_state:
            failed = True

    db.session.add_all(wfids)
    if success: master_flow_instance.is_success = True
    if failed: master_flow_instance.is_failed = True

    # Mak old instance as not the current instance
    from_flow_instance.is_current_state = False

    if master_flow_instance.is_success and master_flow_instance.is_failed:
        raise WorkFlowException("Invalid workflow, failed and success states occurred at the same time")
       
    # Proceed to next state success
    return True


def _synch(master_flow_instance,
           instance_by_transition,
           transitions,
           object_by_next_state={},
           condition_function=None,
           args=[],
           kwargs={}):
    # Check if we can proceed from synch source branch
    proceed = True
    if condition_function:
        proceed = condition_function(*args, **kwargs)
    else:
        for t in transitions:
            obj = instance_by_transition[t].ref_object
            cond = t.transition_condition
            model = obj.__class__
            if model.query.filter_by(id=obj.id).filter(text(cond)).count() == 0:
                proceed = False
            if not proceed: break

    # If we can't proceed, just return False
    if not proceed: return False

    next_state_ids = set([t.to_state_id for t in transitions])
    if len(next_state_ids) > 1:
        raise SynchTypeException("With Synchronization flow type, you must have the same destination state")

    next_state_id = next_state_ids.pop()
    next_state = WorkFlowState.query.filter(WorkFlowState.id == next_state_id).first()

    if proceed is not True and\
       next_state.name != proceed:
        return False

    # We can't use old object because there are more than one, but we need only single next state object
    next_state_object = object_by_next_state.get(next_state.name)
    if not next_state_object:
        raise SynchTypeException("With Synchronization flow type, you must predefine next ref data object")
        

    # Create new flow instance detail as current state instance, which refer to next_state_object
    if next_state_object.id is None:
        db.session.add(next_state_object)
        db.session.flush()

    wfid = WorkFlowInstanceDetail(
        work_flow_instance = master_flow_instance,
        work_flow_state = next_state,
        ref_object = next_state_object,
        is_current_state = True,
        active = True,
    )
    db.session.add(wfid)

    # Disable old current state
    for t in transitions:
        i = instance_by_transition[t]
        i.is_current_state = False

    # Check if flow is success of fail
    if next_state.is_success_state:
        master_flow_instance.is_success = True
    if next_state.is_failed_state:
        master_flow_instance.is_failed = True

    # Proceed to next state success
    return True

def _choice(master_flow_instance,
            instance_by_transition,
            transitions,
            object_by_next_state,
            condition_function=None,
            args=[],
            kwargs={}):
    s = set([instance_by_transition[t] for t in transitions]) # All of transitions must have the same detail_instance
    if len(s) != 1:
        raise ChoiceTypeException("With exclusive choice flow type, you must have only one source state")
    from_flow_instance  = s.pop()

    # Check if we can proceed all split branch (actually, it should be used the same condition for split)
    obj = from_flow_instance.ref_object
    next_state = None
    if condition_function:
        state_by_name = dict([(t.to_state.name, t.to_state) for t in transitions])
        result = condition_function(*args, **kwargs)  # NOTE: Must return next state name
        next_state = state_by_name.get(result)
        
    else:
        for t in transitions:
            cond = t.transition_condition.strip()
            model = obj.__class__
            if model.query.filter_by(id=obj.id).filter(text(cond)).count() == 0:
                continue
            next_state = t.to_state
            break

    if next_state:
        next_state_object = object_by_next_state.get(next_state.name)
        if not next_state_object:
            next_state_object = obj

        if next_state_object.id is None:
            db.session.add(next_state_object)
            db.session.flush()

        wfid = WorkFlowInstanceDetail(
            work_flow_instance = master_flow_instance,
            work_flow_state = next_state,
            ref_object = next_state_object,
            is_current_state = True,
            active = True,
        )
        db.session.add(wfid)

        from_flow_instance.is_current_state = False

        if next_state.is_success_state:
            master_flow_instance.is_success = True
        if next_state.is_failed_state:
            master_flow_instance.is_failed = True
        return True

    return False

def _merge(master_flow_instance,
           instance_by_transition,
           transitions,
           object_by_next_state,
           condition_function=None,
           args=[],
           kwargs={}):
    # Check if we can proceed all split branch (actually, it should be used the same condition for split)
    next_state = None
    if condition_function:
        result = condition_function(*args, **kwargs)  # NOTE: Must return next state name
        to_state = transitions[0].to_state
        if result is True:
            next_state = to_state
        elif result == to_state.name:
            next_state = to_state

    else:
        for t in transitions:
            cond = t.transition_condition.strip()
            obj = instance_by_transition[t].ref_object
            model = obj.__class__
            if model.query.filter_by(id=obj.id).filter(text(cond)).count() == 0:
                continue
            next_state = t.to_state
            break

    if next_state:
        next_state_obj = object_by_next_state.get(next_state.name)
        if not next_state_obj:
            from_instance = instance_by_transition[t]
            next_state_obj = from_instance.ref_object

        if next_state_obj.id is None:
            db.session.add(next_state_obj)
            db.session.flush()

        wfid = WorkFlowInstanceDetail(
            work_flow_instance = master_flow_instance,
            work_flow_state = next_state,
            ref_object = next_state_obj,
            is_current_state = True,
            active = True,
        )
        db.session.add(wfid)

        if next_state.is_success_state:
            master_flow_instance.is_success = True
        if next_state.is_failed_state:
            master_flow_instance.is_failed = True

        # Disable all old current state instance
        for t in transitions:
            i = instance_by_transition[t]
            i.is_current_state = False
        return True
    return False


def _proceed_next_state(master,
                        detail_by_transition,
                        transitions,
                        object_by_next_state = {},
                        transition_type=TransitionType.Sequence,
                        condition_function=None,
                        args=[],
                        kwargs={}):

    if transition_type == TransitionType.Sequence:
        if len(transitions) != 1:
            raise SequenceTypeException("With sequence flow type, you must have only a single transition to be processed")
        return _sequence(master,
                         detail_by_transition,
                         transitions,
                         object_by_next_state,
                         condition_function,
                         args,
                         kwargs)
            
    if transition_type == TransitionType.Split:
        if len(transitions) < 2:
            raise SplitTypeException("With split flow type, you must have more than one transitions to be processed")
        return _split(master,
                      detail_by_transition,
                      transitions,
                      object_by_next_state,
                      condition_function,
                      args,
                      kwargs)

    if transition_type == TransitionType.Synch:
        if len(transitions) < 2:
            raise SynchTypeException("With synch flow type, you must have more than one transitions to be processed")
        return _synch(master,
                      detail_by_transition,
                      transitions,
                      object_by_next_state,
                      condition_function,
                      args,
                      kwargs)

    if transition_type == TransitionType.Choice:
        #if len(transitions) != 1:
        #    raise ChoiceTypeException("With choice flow type, you must have only a single transition to be processed")
        return _choice(master,
                       detail_by_transition,
                       transitions,
                       object_by_next_state,
                       condition_function,
                       args,
                       kwargs)

    if transition_type == TransitionType.Merge:
        if len(transitions) < 1:
            raise MergeTypeException("With merge flow type, you must have at least one transition to be processed")
        return _merge(master,
                      detail_by_transition,
                      transitions,
                      object_by_next_state,
                      condition_function,
                      args,
                      kwargs)

    return False


def _save_yml_to_db(yml):

    # Process each work flow
    for name in yml:
        # Create work flow model
        workflow = create_workflow(name)

        states = yml[name].get('states', [])
        state_by_name = {}
        for state in states:
            # Create each work flow state
            st = add_workflow_state(workflow,
                                    state['name'],
                                    state['model'],
                                    initial_state=state.get('is_initial_state', False),
                                    success_state=state.get('is_success_state', False),
                                    fail_state=state.get('is_fail_state', False))
            state_by_name[st.name] = st

        transitions = yml[name].get('transitions', {})
        for tname in transitions:
            t = transitions[tname]

            from_states = t.get('from_state', [])
            if type(from_states) is not list:
                from_states = [from_states]

            to_states = t.get('to_state', [])
            if type(to_states) is not list:
                to_states = [to_states]

            tt = t.get('type', TransitionType.Sequence)
            token = tname

            # Find all pairs between elements of from_states and to_states
            for state_pair in itertools.product(from_states, to_states):
                n = "{name}__{from_state}_to_{to_state}".format(name=tname,from_state=state_pair[0],to_state=state_pair[1])

                cond = None
                if   tt == TransitionType.Sequence:
                    cond = t['condition']
                elif tt == TransitionType.Split:
                    #cond = t['condition'][state_pair[1]]
                    cond = t['condition']
                    if type(cond) is dict:
                        cvs = set(cond.values())
                        if len(cvs) != 1:
                            raise SplitTypeException("Split transition must have only one condition")
                        cond = cvs.pop()
                        
                elif tt == TransitionType.Synch:
                    cond = t['condition'][state_pair[0]]
                elif tt == TransitionType.Choice:
                    cond = t['condition'][state_pair[1]]
                    #token = n   # Why do we split each choice's transition?
                elif tt == TransitionType.Merge:
                    cond = t['condition'][state_pair[0]]
                else:
                    raise WorkFlowException("Invalid workflow transition type")

                # Create each work flow transition
                fst = state_by_name[state_pair[0]]
                tst = state_by_name[state_pair[1]]
                add_workflow_transition(workflow,
                                        name=n,
                                        from_state=fst,
                                        to_state=tst,
                                        transition_type=tt,
                                        transition_condition=cond,
                                        transition_token=token)
    return True


###############################################
# Callable functions for perform work-flow
###############################################
def init_new_flow(workflow, name, obj_by_state = {}):
    # Find all init states of workflow
    init_states = WorkFlowState.query.filter_by(work_flow_id = workflow.id).\
                    filter_by(is_initial_state=True).\
                    filter_by(active=True).\
                    all()

    # Create instance master
    wfi = WorkFlowInstance(
        work_flow = workflow,
        name = name,
        is_success = False,
        is_failed = False,
        active = True,
    )
                   
    # Create instance details
    # Find all model instances related to all init states
    wfids = []
    for i in init_states:
        model_inst = obj_by_state.get(i.name)
        if model_inst is None:
            raise InitModelInstanceException("Please provide instance of model '%s' for initial flow state '%s'" %(i.model, i.name))

        # Create workflow instance and log
        if model_inst.id is None:
            db.session.add(model_inst)
            db.session.flush()

        wfid = WorkFlowInstanceDetail(
            work_flow_instance = wfi,
            work_flow_state = i,
            ref_object = model_inst,
            is_current_state = True,
            active = True,
        )
        wfids.append(wfid)

    db.session.add(wfi)
    db.session.add_all(wfids)
    return wfi

       
def proceed_flow(workflow_instance, inst_by_next_state={}, states=[], partial_state=None, function=None, args=[], kwargs={}):
    # Checking before doing job
    if workflow_instance.is_success or workflow_instance.is_failed:
        # WorkFlow reached final state already
        return False

    # Find all detail instances
    details = workflow_instance.current_details

    # Group transition token to test whether transition can be occurred or not
    transitions = []
    detail_by_transition = {}
    transition_by_token = {}
    state_by_token = {}
    for d in details:
        new_trans = d.work_flow_state.out_transitions
        transitions.extend(new_trans)
        for t in new_trans:
            detail_by_transition[t] = d
            transition_by_token.setdefault(t.transition_token, []).append(t)
            state_by_token.setdefault(t.transition_token, []).append(d.work_flow_state.name)

    # Make transitions
    # Checking if new state require new model instance, we must provide it
    from_states = set(states)
    results = []
    for token in transition_by_token:
        ts = transition_by_token[token]

        # Check if valid from states
        if partial_state is not None:
            current_states = set(state_by_token.get(token, []))
            result_states  = from_states.intersection(current_states)

            if partial_state is True and\
               len(result_states) == 0:
                # There is not a state to be processed in current round
                continue
            elif partial_state is False and\
                 not current_states.issubset(from_states):
                # All states for a transition must be specified, otherwise, skip
                continue
            elif partial_state is False and\
                 len(result_states) == 0:
                continue

        transition_types =  set([t.transition_type for t in ts])
        if len(transition_types) != 1:
            raise NotUniqueTransitionTypeException("For each transition group, there must be only single transition type")
        result = _proceed_next_state(workflow_instance,
                                     detail_by_transition,
                                     ts,
                                     inst_by_next_state,
                                     ts[0].transition_type,
                                     function,
                                     args,
                                     kwargs)
        results.append(result)

    if not results: return False
    if True in results: # At least one state proceeded, transition success
        return True
    
    return False


# No locking state
def proceed_flow_decorator(function):
    def wrapper(*args, **kwargs):
        workflow_instance = kwargs.get('workflow_instance')
        if workflow_instance is None or\
           type(workflow_instance) is not WorkFlowInstance or\
           workflow_instance.id is None:
            raise WorkFlowException("With decorated transition condition, you must provide instance of WorkFlowInstance model as an argument name 'workflow_instance'")
        inst_by_next_state = kwargs.get('object_by_next_state')
        if inst_by_next_state is None:
            raise WorkFlowException("With decorated transition condition, you must specify dict name 'object_by_next_state', for mapping between next state name and reference object")
        return proceed_flow(workflow_instance, inst_by_next_state, [], None, function, args, kwargs)
    return wrapper


# With locking states, you must define all corresponding state, otherwise, flow could not be proceeded
# states: specify all current states you want to make transition from
# allow_partial: flag to decide whether to proceed flow if presented states are merely partial of them
#   For example: you need stateM stateO and stateP together to proceed with synch transition
#                if allow_partial = True, you need to specify all of them for states
#                if allow_partial = False, you just specify at least one of them
def proceed_flow_decorator_from_state(states=[], allow_partial=False):
    def actual_decorator(function):
        def wrapper(*args, **kwargs):
            workflow_instance = kwargs.get('workflow_instance')
            if workflow_instance is None or\
               type(workflow_instance) is not WorkFlowInstance or\
               workflow_instance.id is None:
                raise WorkFlowException("With decorated transition condition, you must provide instance of WorkFlowInstance model as an argument name 'workflow_instance'")
            inst_by_next_state = kwargs.get('object_by_next_state')
            if inst_by_next_state is None:
                raise WorkFlowException("With decorated transition condition, you must specify dict name 'object_by_next_state', for mapping between next state name and reference object")
            if allow_partial not in [True, False]:
                raise WorkFlowException("You have to specify 'allow_partial' argument with True or False value")

            return proceed_flow(workflow_instance, inst_by_next_state, states, allow_partial, function, args, kwargs)
        return wrapper
    return actual_decorator


def import_work_flow_from_yml(yml_file):
    ymlf = open(yml_file, 'r')
    yml = yaml.load(ymlf.read())
    ymlf.close()
    _save_yml_to_db(yml)
    
if __name__ == '__main__':
    pass
