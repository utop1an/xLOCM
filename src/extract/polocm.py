""".. 'include':: ../../docs/templates/extract/locm.md"""

from collections import defaultdict
from dataclasses import asdict, dataclass
from pprint import pprint
from typing import Dict, List, NamedTuple, Optional, Set, Tuple, Union
from warnings import warn
import networkx as nx
import pulp as pl
from tabulate import tabulate

from traces import Action, PlanningObject

from utils.helpers import *

from observation import ActionObservation, Observation, ObservedTraceList
from .learned_action import LearnedLiftedAction
from .model import Model
from .exceptions import IncompatibleObservationToken
from .learned_fluent import LearnedLiftedFluent


@dataclass
class AP:
    """Action.Position (of object parameter). Position is 1-indexed."""

    action: Action
    pos: int  # NOTE: 1-indexed
    sort: int

    def __repr__(self) -> str:
        return f"{self.action.name}.{self.pos}"

    def __hash__(self):
        return hash(self.action.name + str(self.pos))

    def __eq__(self, other):
        return hash(self) == hash(other)
    
@dataclass
class IAP:
    """Indexed Action.Position (of object parameter). Position is 1-indexed."""

    action: Action
    ind: int # NOTE: index of Action in the Trace
    pos: int  # NOTE: 1-indexed
    sort: int

    def __repr__(self) -> str:
        ending = f".{self.pos}" if self.pos else ""
        return f"[{self.ind}]{self.action.name}{ending}"

    def __hash__(self):
        return hash(self.action.name + str(self.ind) + str(self.pos))

    def __eq__(self, other):
        return hash(self) == hash(other)
    
    def toIndexedAction(self):
        return IAP(self.action, self.ind, None,None)
    
    def toAP(self):
        return AP(self.action, self.pos, self.sort)

@dataclass
class IndexedAction:
    """
    
    """
    action: Action
    ind: int

    def __repr__(self) -> str:
        return f"{self.action.name}[{self.ind}]"

    def __hash__(self):
        return hash(self.action.name + str(self.ind))

    def __eq__(self, other):
        return hash(self) == hash(other)
    
@dataclass
class Transition:
    from_ap: IndexedAction | IAP
    to_ap: IndexedAction | IAP

    def __repr__(self) -> str:
        pass

    def __hash__(self):
        return hash(self.from_ap.__hash__() + self.to_ap.__hash__())

    def __eq__(self, other):
        return hash(self) == hash(other) 

@dataclass
class FSM:
    sort: int
    index: int

    def __repr__(self) -> str:
        return f"FSM.{self.index} @ Sort.{self.sort}"
    
    def __hash__(self):
        return hash((self.sort, self.index))
    
    def __eq__(self, value: object) -> bool:
        return hash(self) == hash(value)

class StatePointers(NamedTuple):
    start: int
    end: int

    def __repr__(self) -> str:
        return f"({self.start} -> {self.end})"


Sorts = Dict[str, int]  # {obj_name: sort}
APStatePointers = Dict[FSM, Dict[AP, StatePointers]]  # {FSM: {AP: APStates}}

OSType = Dict[FSM, List[Set[int]]]  # {FSM: [{states}]}
TSType = Dict[FSM, Dict[PlanningObject, List[AP]]]  # {FSM: {obj: [AP]}}


@dataclass
class HSIndex:
    B: AP
    k: int
    C: AP
    l: int

    def __hash__(self) -> int:
        # NOTE: AP is hashed by action name + pos
        # i.e. the same actions but operating on different objects (in the same pos)
        # will be hashed the same
        # This prevents duplicate hypotheses for an A.P pair
        # e.g. B1=AP(action=<action on G obj1>, pos=1), B2=AP(action=<action on G obj2>, pos=1)
        # with the same k,l, and C (similarly for C) will be hashed the same
        return hash(
            (
                self.B,
                self.k,
                self.C,
                self.l,
            )
        )


@dataclass
class HSItem:
    S: int
    k_: int
    l_: int
    G: int
    G_: int
    supported: bool
    fsm: FSM

    def __hash__(self) -> int:
        return hash((self.S, self.k_, self.l_, self.G, self.G_))


@dataclass
class Hypothesis:
    """Relational hypothesis data structure from the paper.
    S = state shared between the two transitions
    B = action name of the prior transition
    k = shared transition argument position of the prior transition
    k_ = hypothesised shared parameter argument position of the prior transition
    C = action name of the latter transition
    l = shared transition argument position of the latter transition
    l_ = hypothesised shared parameter argument position of the latter transition
    G = sort of the shared parameter
    G_ = sort of the hypothesised shared parameter

    "In general, there is a state S between two consecutive transitions B.k and
    C.l within the FSM associated with sort G, that is where B moves an object O
    of sort G into S, and C moves O out of S. When both actions B and C contain
    another argument of the same sort G′ in position k′ and l′ respectively, we
    hypothesise that there may be a relation between sorts G and G′."
    """
    S: int
    B: AP
    k: int
    k_: int
    C: AP
    l: int
    l_: int
    G: int
    G_: int
    fsm: FSM

    def __hash__(self) -> int:
        return hash(
            (
                self.S,
                self.B,
                self.k,
                self.k_,
                self.C,
                self.l,
                self.l_,
                self.G_,
            )
        )

    def __repr__(self) -> str:
        out = "<\n"
        for k, v in asdict(self).items():
            out += f"  {k}={v}\n"
        return out.strip() + "\n>"

    @staticmethod
    def from_dict(
        hs: Dict[HSIndex, Set[HSItem]]
    ) -> Dict[FSM, Dict[int, Set["Hypothesis"]]]:
        """Converts a dict of HSIndex -> HSItem to a dict of G -> S -> Hypothesis"""
        HS: Dict[FSM, Dict[int, Set["Hypothesis"]]] = defaultdict(
            lambda: defaultdict(set)
        )
        for hsind, hsitems in hs.items():
            hsind = hsind.__dict__
            for hsitem in hsitems:
                hsitem_dict = hsitem.__dict__
                hsitem_dict.pop("supported")
                HS[hsitem.fsm][hsitem.S].add(Hypothesis(**{**hsind, **hsitem_dict}))
        return HS


Hypotheses = Dict[FSM, Dict[int, Set[Hypothesis]]]  # {FSM: {state: [Hypothesis]}}


Binding = NamedTuple("Binding", [("hypothesis", Hypothesis), ("param", int)])
Bindings = Dict[FSM, Dict[int, List[Binding]]]  # {FSM: {state: [Binding]}}

Statics = Dict[str, List[str]]  # {action: [static preconditions]}


class POLOCM:
    """LOCM"""

    zero_obj = PlanningObject("zero", "zero")

    def __new__(
        cls,
        obs_tracelist: ObservedTraceList,
        statics: Optional[Statics] = None,
        viz: bool = False,
        view: bool = False,
        debug: Union[bool, Dict[str, bool], List[str]] = False,
    ):
        """Creates a new Model object.
        Args:
            observations (ObservationList):
                The state observations to extract the model from.
            statics (Dict[str, List[str]]):
                A dictionary mapping an action name and its arguments to the
                list of static preconditions of the action. A precondition should
                be a tuple, where the first element is the predicate name and the
                rest correspond to the arguments of the action (1-indexed).
                E.g. static( next(C1, C2), put_on_card_in_homecell(C2, C1, _) )
                should is provided as: {"put_on_card_in_homecell": [("next", 2, 1)]}
            viz (bool):
                Whether to visualize the FSM.
            view (bool):
                Whether to view the FSM visualization.

        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if obs_tracelist.type is not ActionObservation:
            raise IncompatibleObservationToken(obs_tracelist.type, POLOCM)

        if isinstance(debug, bool) and debug:
            debug = defaultdict(lambda: True)
        elif isinstance(debug, dict):
            debug = defaultdict(lambda: False, debug)
        elif isinstance(debug, list):
            debug = defaultdict(lambda: False, {k: True for k in debug})
        else:
            debug = defaultdict(lambda: False)

        obs_trace = obs_tracelist[0]
        fluents, actions = None, None

        sorts = POLOCM._get_sorts(obs_tracelist, debug=debug["get_sorts"])

        if debug["sorts"]:
            print(f"Sorts:\n{sorts}", end="\n\n")


        
        TS, ap_state_pointers, OS = POLOCM._step1(obs_trace, sorts, debug["step1"])
        HS = POLOCM._step3(TS, ap_state_pointers, OS, sorts, debug["step3"])
        bindings = POLOCM._step4(HS, debug["step4"])
        bindings = POLOCM._step5(HS, bindings, debug["step5"])
        fluents, actions = POLOCM._step7(
            OS,
            ap_state_pointers,
            sorts,
            bindings,
            statics if statics is not None else {},
            debug["step7"],
        )

        if viz:
            state_machines = POLOCM.get_state_machines(ap_state_pointers, OS, bindings)
            for sm in state_machines:
                sm.render(view=view)

        return Model(fluents, actions)

    @staticmethod
    def _get_sorts(obs_tracelist: ObservedTraceList, debug=False) -> Sorts:
        sorts = []  # initialize list of sorts for this trace
        # track actions seen in the trace, and the sort each actions params belong to
        ap_sort_pointers: Dict[str, List[int]] = {}
        # track objects seen in the trace, and the sort each belongs to
        # obj_sort_pointers: Dict[str, int] = {}
        sorted_objs = []

        def get_obj_sort(obj: PlanningObject) -> int:
            """Returns the sort index of the object"""
            for i, sort in enumerate(sorts):
                if obj in sort:
                    return i
            raise ValueError(f"Object {obj} not in any sort")
        
        for obs_trace in obs_tracelist:
            for obs in obs_trace:
                action = obs.action
                if action is None:
                    continue

                if debug:
                    print("\n\naction:", action.name, action.obj_params)

                if action.name not in ap_sort_pointers:  # new action
                    if debug:
                        print("new action")

                    ap_sort_pointers[action.name] = []

                    # for each parameter of the action
                    for obj in action.obj_params:
                        if obj.name not in sorted_objs:  # unsorted object
                            # append a sort (set) containing the object
                            sorts.append({obj})

                            # record the object has been sorted and the index of the sort it belongs to
                            obj_sort = len(sorts) - 1
                            sorted_objs.append(obj.name)
                            ap_sort_pointers[action.name].append(obj_sort)

                            if debug:
                                print("new object", obj.name)
                                print("sorts:", sorts)

                        else:  # object already sorted
                            # look up the sort of the object
                            obj_sort = get_obj_sort(obj)
                            ap_sort_pointers[action.name].append(obj_sort)

                            if debug:
                                print("sorted object", obj.name)
                                print("sorts:", sorts)

                    if debug:
                        print("ap sorts:", ap_sort_pointers)

                else:  # action seen before
                    if debug:
                        print("seen action")

                    for ap_sort, obj in zip(
                        ap_sort_pointers[action.name], action.obj_params
                    ):
                        if debug:
                            print("checking obj", obj.name)
                            print("ap sort:", ap_sort)

                        if obj.name not in sorted_objs:  # unsorted object
                            if debug:
                                print("unsorted object", obj.name)
                                print("sorts:", sorts)

                            # add the object to the sort of current action parameter
                            sorts[ap_sort].add(obj)
                            sorted_objs.append(obj.name)

                        else:  # object already has a sort
                            # retrieve the sort the object belongs to
                            obj_sort = get_obj_sort(obj)

                            if debug:
                                print(f"retrieving sorted obj {obj.name}")
                                print(f"obj_sort_idx: {obj_sort}")
                                print(f"seq_sorts: {sorts}")

                            # check if the object's sort matches the action paremeter's
                            # if so, do nothing and move on to next step
                            # otherwise, unite the two sorts
                            if obj_sort == ap_sort:
                                if debug:
                                    print("obj sort matches action")
                            else:
                                if debug:
                                    print(
                                        f"obj sort {obj_sort} doesn't match action {ap_sort}"
                                    )
                                    print(f"seq_sorts: {sorts}")

                                # unite the action parameter's sort and the object's sort
                                sorts[obj_sort] = sorts[obj_sort].union(sorts[ap_sort])

                                # drop the not unionized sort
                                sorts.pop(ap_sort)

                                old_obj_sort = obj_sort

                                obj_sort = get_obj_sort(obj)

                                if debug:
                                    print(
                                        f"united seq_sorts[{ap_sort}] and seq_sorts[{obj_sort}]"
                                    )
                                    print(f"seq_sorts: {sorts}")
                                    print(f"ap_sort_pointers: {ap_sort_pointers}")
                                    print("updating pointers...")

                                min_idx = min(ap_sort, obj_sort)

                                # update all outdated records of which sort the affected objects belong to
                                for action_name, ap_sorts in ap_sort_pointers.items():
                                    for p, sort in enumerate(ap_sorts):
                                        if sort == ap_sort or sort == old_obj_sort:
                                            ap_sort_pointers[action_name][p] = obj_sort
                                        elif sort > min_idx:
                                            ap_sort_pointers[action_name][p] -= 1

                                if debug:
                                    print(f"ap_sort_pointers: {ap_sort_pointers}")
            
        obj_sorts = {}
        for i, sort in enumerate(sorts):
            for obj in sort:
                # NOTE: object sorts are 1-indexed so the zero-object can be sort 0
                obj_sorts[obj.name] = i + 1

        return obj_sorts

    @staticmethod
    def _pointer_to_set(states: List[Set], pointer, pointer2=None) -> Tuple[int, int]:
        """
        from pointer to state?
        """
        state1, state2 = None, None
        for i, state_set in enumerate(states):
            if pointer in state_set:
                state1 = i
            if pointer2 is None or pointer2 in state_set:
                state2 = i
            if state1 is not None and state2 is not None:
                break

        assert state1 is not None, f"Pointer ({pointer}) not in states: {states}"
        assert state2 is not None, f"Pointer ({pointer2}) not in states: {states}"
        return state1, state2
    
    @staticmethod
    def polocm_step1(
        obs_PO_tracelist: ObservedTraceList,
        sorts: Sorts,
        debug: bool= False
    ):  
        """
        Build PO matrices
        """
        # TODO: add zero obj
        sort_aps:Dict[int, Set[AP]] = defaultdict(set)
        # obj_traces for all obs_traces in obs_tracelist, indexed by trace_no
        obj_PO_trace_overall = []
        trace_PO_matrix_overall = []
        for obs_PO_trace in obs_PO_tracelist:
            indexed_actions = [IAP(obs.action, obs.index, None, None) for obs in obs_PO_trace]
            traces_PO_matrix = pd.DataFrame(columns=indexed_actions, index=indexed_actions)
            # collect action sequences for each object
            obj_PO_traces: Dict[PlanningObject, List[AP]] = defaultdict(list)
            for PO_obs in obs_PO_trace:
                action = PO_obs.action
                if action is not None:
                    # for each combination of action name A and argument pos P
                    for j, obj in enumerate(action.obj_params):
                        # create transition A.P
                        iap = IAP(action, PO_obs.index, pos=j + 1, sort=sorts[obj.name])
                        sort_aps[sorts[obj.name]].add(iap.toAP())
                        obj_PO_traces[obj].append(iap)
                    for successor_ind in PO_obs.successors:
                        successor = obs_PO_trace[successor_ind-1]
                        assert successor != None
                        if PO_obs.index < successor_ind:
                            traces_PO_matrix.at[IAP(action,PO_obs.index, None, None),
                                                IAP(successor.action,successor_ind, None, None)]=1
                        else:
                            traces_PO_matrix.at[IAP(successor.action, successor_ind, None, None),
                                                IAP(PO_obs.action,PO_obs.index, None, None)]=0
            trace_PO_matrix_overall.append(traces_PO_matrix)      
            obj_PO_trace_overall.append(obj_PO_traces)
        
        # constructing PO matrix of actions in each trace
        for trace_PO_matrix in trace_PO_matrix_overall:
            for i in range(len(trace_PO_matrix)):
                for j in range(i+1,len(trace_PO_matrix.columns)):
                    current = trace_PO_matrix.iloc[i,j]
                    
                    # complete matrix based on transitivity of PO
                    # if a>b, b>c, then a>c
                    for x in range(1,len(trace_PO_matrix.columns)- j):
                        next = trace_PO_matrix.iloc[j,j+x]
                        if current == 1 and next == 1:
                            trace_PO_matrix.iloc[i,j+x] =1
                        elif current ==0 and next == 0:
                            trace_PO_matrix.iloc[i,j+x] =0
    
        # Constructing PO matrix of actions for each object in each trace
        obj_trace_PO_matrix_overall = []
        # Initialize FO matrix
        obj_trace_FO_matrix_overall = []
        for trace_no,obj_PO_trace in enumerate(obj_PO_trace_overall):
            PO_matrices: Dict[PlanningObject, pd.DataFrame] = defaultdict()
            FO_matrices: Dict[PlanningObject, pd.DataFrame] = defaultdict()
            for obj, iaps in obj_PO_trace.items():
                obj_trace_PO_matrix = pd.DataFrame(columns=iaps, index=iaps)    
                obj_trace_FO_matrix = pd.DataFrame(columns=iaps, index=iaps)                
                for row_header, row in obj_trace_PO_matrix.iterrows():
                    for col_header, val in row.items():
                        origin = trace_PO_matrix_overall[trace_no].at[row_header.toIndexedAction(),
                                                                      col_header.toIndexedAction()]
                        obj_trace_PO_matrix.at[row_header, col_header] = origin
                        
                PO_matrices[obj] = obj_trace_PO_matrix
                FO_matrices[obj] = obj_trace_FO_matrix  
            obj_trace_PO_matrix_overall.append(PO_matrices)
            obj_trace_FO_matrix_overall.append(FO_matrices)
        
        # Completing FO matrices based on current incomplete PO matrices?
        for trace_no, matrices in enumerate(obj_trace_PO_matrix_overall):
            for obj, PO_matrix in matrices.items():
                FO_matrix = obj_trace_FO_matrix_overall[trace_no][obj]
                for i in range(len(PO_matrix)):
                    for j in range(i+1, len(PO_matrix.columns) ):
                        current_PO = PO_matrix.iloc[i,j]
                        if current_PO == 0:
                            FO_matrix.iloc[i,j] = 0
                        elif current_PO == 1:
                            flag = 1
                            for x in range(len(FO_matrix.columns)):
                                flip = 0
                                if x != i and x !=j:
                                    ix = PO_matrix.iloc[i,x]
                                    if (pd.isna(ix)):
                                        ix = PO_matrix.iloc[x,i]
                                        flip +=1
                                    jx = PO_matrix.iloc[j,x]
                                    if(pd.isna(jx)):
                                        jx = PO_matrix.iloc[x,j]
                                        flip+=1
                                    if (not pd.isna(ix) and not pd.isna(jx)):
                                        if (flip%2==0):
                                            if (ix!=jx):
                                                FO_matrix.iloc[i,j] = 0
                                                flag=0 
                                                break
                                        else:
                                            if(ix == jx):
                                                FO_matrix.iloc[i,j] = 0
                                                flag=0
                                                break

                                    else:
                                        flag = 0
                                        break
                            if flag:
                                FO_matrix.iloc[i,j]=1

                                

        if debug:
            printmd("# Step 1")
            printmd("## Obj PO traces:\n")
            for i, obj_PO_traces in enumerate(obj_PO_trace_overall):
                printmd(f"### Trace **{i}**\n")
                print(tabulate(obj_PO_traces, headers='keys', tablefmt='psql'))

            printmd("## Traces PO Matrix")
            for i, matrix in enumerate(trace_PO_matrix_overall):
                printmd(f"### Trace **{i}**\n")
                print(tabulate(matrix, headers="keys", tablefmt='fancy_grid'))
            
            printmd("## Object Traces PO Matrix")
            for i, matrices in enumerate(obj_trace_PO_matrix_overall):
                printmd(f"### Trace **{i}**\n")
                for obj, matrix in matrices.items():
                    printmd(f"#### Object ***{obj.name}***\n")
                    print(tabulate(matrix, headers="keys", tablefmt='fancy_grid'))
            
            printmd("## Object Traces FO Matrix")
            for i, matrices in enumerate(obj_trace_FO_matrix_overall):
                printmd(f"### Trace {i}\n")
                for obj, matrix in matrices.items():
                    printmd(f"#### Object {obj.name}\n")
                    print(tabulate(matrix, headers="keys", tablefmt='fancy_grid'))
        return obj_PO_trace_overall, trace_PO_matrix_overall, obj_trace_PO_matrix_overall, obj_trace_FO_matrix_overall, sort_aps

    @staticmethod
    def polocm_step2(
        trace_PO_matrix_overall,
        obj_trace_PO_matrix_overall,
        LP_var_type = "trace",
        debug = False
        ):
    
        PO_matrix_with_vars = obj_trace_PO_matrix_overall.copy()
        prob = pl.LpProblem(LP_var_type + "_var_assignments", sense=pl.LpMinimize)
        PO_vars_overall= []
        constraints: Dict[str, List[str]] = defaultdict(list)
        if (LP_var_type == "trace"):
            
            for trace_no, matrix in enumerate(trace_PO_matrix_overall):
                PO_vars = {}
        
                cols = matrix.columns.tolist()
                rows = matrix.index.tolist()
                for i in range(len(matrix)):
                    for j in range(i+1,len(matrix.columns)):
                        if pd.isna(matrix.iloc[i,j]):
                            var_name = f"trace_{trace_no}_{str(cols[i])}~{str(rows[j])}"
                            var = pl.LpVariable(var_name, cat=pl.LpBinary, upBound=1, lowBound=0) 
                            PO_vars[(cols[i], rows[j])] = var 
                            matrix.iloc[i,j] = (cols[i], rows[j])
                PO_vars_overall.append(PO_vars)
            
            for trace_no, matrices in enumerate(PO_matrix_with_vars):
                PO_vars = PO_vars_overall[trace_no]
                for obj, matrix in matrices.items():
                    for row_header, row in matrix.iterrows():
                        for col_header, val in row.items():
                            key = (row_header.toIndexedAction(), col_header.toIndexedAction())
                            if key in PO_vars.keys():
                                matrix.at[row_header, col_header] = key

            # TODO: updating the obj trace matrix?

        elif (LP_var_type == "obj_trace"):
            for trace_no, matrices in enumerate(PO_matrix_with_vars):
                PO_vars = {}
                for obj, matrix in matrices.items():
                    for row_header, row in matrix.iterrows():
                        for col_header, val in row.items():
                            var_name= f"obj_trace_{trace_no}_{str(row_header)}~{str(col_header)}"
                            var = pl.LpVariable(var_name, cat=pl.LpBinary, upBound=1, lowBound=0) 
                            PO_vars[(row_header, col_header)] = var 
                            matrix.at[row_header, col_header] = (row_header, col_header)
            PO_vars_overall.append(PO_vars)

        # adding constraints on transitivity
        for trace_no, matrices in enumerate(PO_matrix_with_vars):
            PO_vars = PO_vars_overall[trace_no]
            for obj, matrix in matrices.items():
                for i in range(len(matrix)):
                    for j in range(i+1, len(matrix.columns)):
                        for x in range(1,len(matrix.columns)- j):
                            
                            current = PO_vars.get(matrix.iloc[i,j], matrix.iloc[i,j])
                            next = PO_vars.get(matrix.iloc[j, j+x],matrix.iloc[j, j+x])
                            target = PO_vars.get(matrix.iloc[i, j+x],matrix.iloc[i, j+x])

                            if (isinstance(current, pl.LpVariable) or isinstance(next, pl.LpVariable) or isinstance(target, pl.LpVariable)):
                                prob += target >= current + next -1 # a>b, b>c, then a>c
                                prob += target <= current + next  # a<b. b<c, then a<c
                                if debug:
                                    constraints[f'Trace {trace_no}'].append(f"{target} >= {current} + {next} - 1")
                                    constraints[f'Trace {trace_no}'].append(f"{target} <= {current} + {next}")
        
        if debug:
            printmd("# Step 2")
            printmd("## PO vars")
            for trace_no, PO_vars in enumerate(PO_vars_overall):
                printmd(f"### Trace {trace_no}")
                pprint(PO_vars)

            printmd("## PO matrix with vars")
            for trace_no, matrices in enumerate(PO_matrix_with_vars):
                printmd(f"### Trace {trace_no}")
                for obj, matrix in matrices.items():
                    printmd(f"#### Obj {obj.name}")
                    print(tabulate(matrix, headers="keys", tablefmt="fancy_grid"))

            printmd("## PO Constraints")
            print(tabulate(constraints, headers="keys", tablefmt="fancy_grid"))
        return prob, PO_vars_overall, PO_matrix_with_vars


    @staticmethod
    def polocm_step3(
        prob,
        PO_vars_overall,
        PO_matrix_with_vars,
        obj_trace_FO_matrix_overall,
        debug= False
    ):
        constraints: Dict[str, List[str]] = defaultdict(list)
        FO_matrix_with_vars = obj_trace_FO_matrix_overall.copy()
        FO_vars_overall = []
        varname_lookup = defaultdict()
        for trace_no, matrices in enumerate(PO_matrix_with_vars):
            FO_vars: Dict[PlanningObject, Dict[tuple, pl.LpVariable]] = defaultdict(dict)
            for obj, PO_matrix in matrices.items():
                cols = PO_matrix.columns.tolist()
                rows = PO_matrix.index.tolist()
                FO_matrix = FO_matrix_with_vars[trace_no][obj]
                for i in range(len(PO_matrix)-1):
                    for j in range(i+1, len(PO_matrix)):
                        flag = 0
                        current_PO = PO_vars_overall[trace_no].get(PO_matrix.iloc[i,j],PO_matrix.iloc[i,j])
                        if (pd.isna(FO_matrix.iloc[i,j])):
                            flag = 1
                            var_name = f"FO_{trace_no}_{str(obj.name)}_{str(cols[i])}~{str(rows[j])}"
                            var = pl.LpVariable(var_name, cat=pl.LpBinary, upBound=1, lowBound=0) 
                            FO_vars[obj][(cols[i], rows[j])] = var 
                            FO_matrix.iloc[i,j] = (cols[i], rows[j])
                            varname_lookup[var_name] = (trace_no, obj, cols[i], rows[j])
                            prob += var <= current_PO # if PO == 0, then FO = 0; if PO==1, then FO = 1 or 0
                            if (debug):
                                constraints[f"Trace {trace_no} - Dependency"].append(f"{var} <= {current_PO}")
                            candidates = []
                            for x in range(len(FO_matrix.columns)):
                                flip = 0
                                if (x!=i and x!=j):
                                    ix = PO_vars_overall[trace_no].get(PO_matrix.iloc[i,x],PO_matrix.iloc[i,x])
                                    jx = PO_vars_overall[trace_no].get(PO_matrix.iloc[j,x],PO_matrix.iloc[j,x])
                                    if (pd.isna(ix)):
                                        ix = PO_vars_overall[trace_no].get(PO_matrix.iloc[x,i],PO_matrix.iloc[x,i])
                                        flip+=1
                                    if(pd.isna(jx)):
                                        jx = PO_vars_overall[trace_no].get(PO_matrix.iloc[x,j],PO_matrix.iloc[x,j])
                                        flip+=1
                                    if (isinstance(ix, pl.LpVariable) or isinstance(jx, pl.LpVariable) or flag):
                                        aux = pl.LpVariable(f"aux_{str(trace_no)}_{str(obj)}_{i}_{j}_{x}", cat=pl.LpBinary)
                                        if(flip%2==0):
                                            prob += aux <= 1-ix+jx
                                            prob += aux <= 1-jx+ix
                                            prob += aux >= 1-ix-jx
                                            prob += aux >= ix+jx-1
                                        else:
                                            prob += aux >= ix-jx
                                            prob += aux >= jx-ix
                                            prob += aux <= ix+jx
                                            prob += aux <= 2-(ix+jx)
                                        prob += var <= aux
                                        candidates.append(aux)
                                        if debug:
                                            constraints[f"Trace {trace_no} - AUX 0"].append(f"{var} <= aux_i{i}j{j}x{x}")
                            if (len(candidates)>0):
                                prob += var >= pl.lpSum(candidates) - len(candidates) + 1
                                if (debug):
                                    constraints[f"Trace {trace_no} - AUX 1"].append(f"{var} >= {[can for can in candidates]} - {len(candidates)-1}")
            FO_vars_overall.append(FO_vars)
        for trace_no, matrices in enumerate(FO_matrix_with_vars):
            for obj, FO_matrix in matrices.items():
                FO_vars = FO_vars_overall[trace_no][obj]
                for m in range(len(FO_matrix)-1):
                    prob += pl.lpSum(FO_vars.get(FO_matrix.iloc[m,n],FO_matrix.iloc[m,n]) for n in range(m+1, len(FO_matrix))) == 1 # every row sum == 1
                    if debug:
                        constraints[f"Trace {trace_no} - ROWSUM"].append(f"{[FO_vars.get(FO_matrix.iloc[m,n],FO_matrix.iloc[m,n]) for n in range(m+1, len(FO_matrix))]} == 1")
                for l in range(1,len(FO_matrix)):
                    prob += pl.lpSum(FO_vars.get(FO_matrix.iloc[k,l] ,FO_matrix.iloc[k,l] ) for k in range(l)) == 1 # every col sum == 1
                    if debug:
                        constraints[f"Trace {trace_no} - COLSUM"].append(f"{[FO_vars.get(FO_matrix.iloc[k,l] ,FO_matrix.iloc[k,l] ) for k in range(l)]} == 1")
        if debug:
            printmd("# Step 3")
            printmd("## FO vars")
            for trace_no, FO_vars in enumerate(FO_vars_overall):
                printmd(f"### Trace {trace_no}")
                print(tabulate(FO_vars, headers="keys", tablefmt="fancy_grid"))

            printmd("## FO matrix with vars")
            for trace_no, matrices in enumerate(FO_matrix_with_vars):
                printmd(f"### Trace {trace_no}")
                for obj, matrix in matrices.items():
                    printmd(f"#### Obj {obj.name}")
                    print(tabulate(matrix, headers="keys", tablefmt="fancy_grid"))

            printmd("## FO Constraints")
            print(tabulate(constraints, headers="keys", tablefmt="fancy_grid"))
        
        return prob, FO_vars_overall, FO_matrix_with_vars, varname_lookup
                                    

    def polocm_step4(
        prob,
        sort_aps,
        sorts,
        FO_vars_overall,
        FO_matrix_with_vars,
        varname_lookup,
        debug = False
    ):
        constraints: Dict[int, List[str]] = defaultdict(list)
        _sort_transition_matrix: Dict[int, pd.DataFrame] = defaultdict()
        sort_transition_matrix: Dict[int, pd.DataFrame] = defaultdict()
        for sort, aps in sort_aps.items():
            cols = list(aps)
            transition_matrix = pd.DataFrame(columns=cols, index=cols)
            _sort_transition_matrix[sort] = transition_matrix.copy()
            sort_transition_matrix[sort] = transition_matrix.copy()
        
        for trace_no, matrices in enumerate(FO_matrix_with_vars):
            for obj, matrix in matrices.items():
                 cols = matrix.columns.tolist()
                 for i in range(len(matrix)):
                    for j in range(i+1, len(matrix.columns) ):
                        from_ap = cols[i].toAP()
                        to_ap = cols[j].toAP()
                        if (pd.isna(_sort_transition_matrix[sorts[obj.name]].at[from_ap, to_ap])):
                            _sort_transition_matrix[sorts[obj.name]].at[from_ap, to_ap] = set()
                        elif (_sort_transition_matrix[sorts[obj.name]].at[from_ap, to_ap] == 1):
                            continue
                        if (isinstance(matrix.iloc[i,j], tuple)):
                            _sort_transition_matrix[sorts[obj.name]].at[from_ap, to_ap].add(FO_vars_overall[trace_no][obj].get(matrix.iloc[i,j],matrix.iloc[i,j]))
                        elif(matrix.iloc[i,j] == 1):
                            _sort_transition_matrix[sorts[obj.name]].at[from_ap, to_ap] = 1
        
        sort_AP_vars: Dict[int, Dict[(AP,AP), pl.LpVariable]] = defaultdict(dict)
        for sort, matrix in sort_transition_matrix.items():
            for row_header, rows in matrix.iterrows():
                for col_header, val in rows.items():
                    if (isinstance(_sort_transition_matrix[sort].at[row_header, col_header], set)):
                        var_name = "AP_" + str(row_header) + "~" + str(col_header)
                        var = pl.LpVariable(var_name, cat=pl.LpBinary, upBound=1, lowBound=0) 
                        sort_AP_vars[sort][(row_header, col_header)] = var
                        matrix.at[row_header, col_header] = (row_header, col_header)
                        varname_lookup[var_name] = (sort, row_header, col_header)

                        for FO_var in _sort_transition_matrix[sort].at[row_header, col_header]:
                            prob += var>= FO_var # exist one
                        if debug:
                            constraints[sort].append(f"{var} >= {[x for x in _sort_transition_matrix[sort].at[row_header, col_header]]}")
                    else:
                        matrix.at[row_header, col_header] = _sort_transition_matrix[sort].at[row_header, col_header]
        
        if debug:
            printmd("# Step 4")
            printmd("## AP vars")
            print(tabulate(sort_AP_vars, headers="keys", tablefmt="fancy_grid"))
                

            printmd("## AP matrix with vars")
            for sort, matrix in sort_transition_matrix.items():
                printmd(f"### Sort {sort}")
                print(tabulate(matrix, headers="keys", tablefmt="fancy_grid"))
                    

            printmd("## AP Constraints")
            print(tabulate(constraints, headers="keys", tablefmt="fancy_grid"))

        return prob, sort_transition_matrix, sort_AP_vars, varname_lookup

    @staticmethod
    def polocm_step5(
        prob,
        solver,
        sort_AP_vars,
        debug = False
    ):
        print(sort_AP_vars)
        prob += pl.lpSum([var for var_list in sort_AP_vars.values() for var in var_list.values()])
        
        prob.solve(solver)
        solution = {var.name: var.varValue for var in prob.variables()}
        if debug:
            print("Solution:")
            pprint(solution)
            print()

            print("Objectives:")
            print(pl.value(prob.objective))
            print()
        
        return solution

    def polocm_step6(
        FO_matrix_with_vars,
        FO_vars_overall,
        sort_transition_matrix,
        AP_vars_overall,
        solution,
        debug= False
    ):
        sol_FO_matrix = FO_matrix_with_vars.copy()
        for trace_no, matrices in enumerate(FO_matrix_with_vars):
            FO_vars: Dict[PlanningObject, Dict[tuple, pl.LpVariable]] = defaultdict(dict)
            for obj, FO_matrix in matrices.items():
                cols = FO_matrix.columns.tolist()
                rows = FO_matrix.index.tolist()
                
                for i in range(len(FO_matrix)-1):
                    for j in range(i+1, len(FO_matrix)):
                        if(isinstance(FO_matrix.iloc[i,j], tuple)):
                            var = FO_vars_overall[trace_no][obj].get(FO_matrix.iloc[i,j])

                            sol_var = solution[var.name]
                            sol_FO_matrix[trace_no][obj].iloc[i,j] = sol_var
        
        sol_AP_matrix = sort_transition_matrix.copy()
        for sort, matrix in sort_transition_matrix.items():
            for i in range(len(matrix)):
                for j in range(len(matrix)):
                    if(isinstance(matrix.iloc[i,j], tuple)):
                        var = AP_vars_overall[sort].get(matrix.iloc[i,j])
                       
                        sol_var = solution[var.name]
                        sol_AP_matrix[sort].iloc[i,j]= sol_var
        if debug:
            printmd("## Solution FO matrix")
            for trace_no, matrices in enumerate(sol_FO_matrix):
                printmd(f"### Trace {trace_no}")
                for obj, matrix in matrices.items():
                    printmd(f"#### Obj {obj.name}")
                    print(tabulate(matrix, headers="keys", tablefmt="fancy_grid"))

            printmd("## Solution AP matrix")
            for sort, matrix in sol_AP_matrix.items():
                printmd(f"### Sort {sort}")
                print(tabulate(matrix, headers="keys", tablefmt="fancy_grid"))

        return sol_FO_matrix, sol_AP_matrix



    @staticmethod
    def _locm2_step1(
        obs_tracelist: ObservedTraceList, sorts: Sorts, debug: bool = False
    ):
        """
        build transition graphs
        """
        # create the zero-object for zero analysis (step 2)
        zero_obj = POLOCM.zero_obj

        graphs = []
        for sort in range(len(set(sorts.values()))+1):
            graphs.append(nx.DiGraph())
        
        # obj_traces for all obs_traces in obs_tracelist, indexed by trace_no
        obj_traces_overall = []
        for obs_trace in obs_tracelist:
            # collect action sequences for each object
            obj_traces: Dict[PlanningObject, List[AP]] = defaultdict(list)
            for obs in obs_trace:
                action = obs.action
                if action is not None:
                    # add the step for the zero-object 
                    zero_ap = AP(action, pos=0, sort=0)
                    obj_traces[zero_obj].append(zero_ap)
                    graphs[0].add_node(zero_ap)
                    # for each combination of action name A and argument pos P
                    for j, obj in enumerate(action.obj_params):
                        # create transition A.P
                        ap = AP(action, pos=j + 1, sort=sorts[obj.name])
                        obj_traces[obj].append(ap)
                        
                        graphs[sorts[obj.name]].add_node(ap)
            obj_traces_overall.append(obj_traces)
        
        # adjacent matrix list for all sorts
        AML = []
        for obj_trace in obj_traces_overall:
            for obj, seq in obj_trace.items():
                sort = sorts[obj.name] if obj.name!='zero' else 0
                for i in range(0, len(seq)-1):
                    
                    if (graphs[sort].has_edge(seq[i], seq[i+1])):
                        graphs[sort][seq[i]][seq[i+1]]['weight']+=1
                    else:
                        graphs[sort].add_edge(seq[i],seq[i+1],weight=1)
        

        for index, G in enumerate(graphs):
            df = nx.to_pandas_adjacency(G, nodelist=G.nodes(), dtype=int)
            AML.append(df)
            if debug:
                print("Sort.{} AML:".format(index))
                print_table(df)
        return AML, obj_traces_overall


    @staticmethod
    def _locm2_step2(
        AML,
        debug = False
    ):
        """
        get adjacency matrix with holes
        """
        AML_with_holes = []
        for index,AM in enumerate(AML):
            df = AM.copy()
            df1 = AM.copy()
            if (index == 0): # zero obj
                AML_with_holes.append(df1)
                continue
            # for particular adjacency matrix's copy, loop over all pairs of rows
            for i in range(df.shape[0] - 1):
                for j in range(i+1, df.shape[0]):
                    idx1, idx2 = i, j
                    row1, row2 = df.iloc[idx1,:], df.iloc[idx2, :] #we have now all pairs of rows

                    common_values_flag = False #for each two rows we have a common_values_flag

                    # if there is a common value between two rows, turn common value flag to true
                    for col in range(row1.shape[0]):
                        if row1.iloc[col] > 0 and row2.iloc[col] > 0:
                            common_values_flag = True
                            break

                    # now if two rows have common values, we need to check for holes.
                    if common_values_flag:
                        for col in range(row1.shape[0]):
                            if row1.iloc[col] > 0 and row2.iloc[col] == 0:
                                df1.iloc[idx2,col] = 'hole'
                            elif row1.iloc[col] == 0 and row2.iloc[col] > 0:
                                df1.iloc[idx1, col] = 'hole'
            if debug:
                print("Sort.{} AML with holes:".format(index))
                print_table(df1)
            AML_with_holes.append(df1)
        return AML_with_holes

    @staticmethod
    def _locm2_step3(
        AML_with_holes,
        debug = False
    ):
        """
        get holes per sort
        """
        # Create list of set of holes per sort (H)
        H_per_sort = []
        for index,df in enumerate(AML_with_holes):
            if index == 0:
                H_per_sort.append(set())
                continue
            holes = set()
            for i in range(df.shape[0]):
                for j in range(df.shape[1]):
                    if df.iloc[i,j] == 'hole':
                        holes.add(frozenset({df.index[i] , df.columns[j]}))
            H_per_sort.append(holes)
            if debug:
                print("#holes in Sort.{}: {}".format(index, len(holes)))
            
        return H_per_sort

    @staticmethod
    def _locm2_step4(
        AML_with_holes,
    ):
        """
        get transitions per sort
        """
        transitions_per_sort = []
        for index, df in enumerate(AML_with_holes):
            transitions_per_sort.append(df.columns.values)
        return transitions_per_sort

    @staticmethod
    def _locm2_step5(
        AML_with_holes
    ):
        """
        get consecutive transitions per sort
        """
        consecutive_transitions_per_sort = []
        for index, df in enumerate(AML_with_holes):
            consecutive_transitions = set()  # for a class
            for i in range(df.shape[0]):
                for j in range(df.shape[1]):
                    if df.iloc[i, j] != 'hole':
                        if df.iloc[i, j] > 0:
    #                         print("(" + df.index[i] + "," + df.columns[j] + ")")
                            consecutive_transitions.add((df.index[i], df.columns[j]))
            consecutive_transitions_per_sort.append(consecutive_transitions)
        return consecutive_transitions_per_sort

    @staticmethod
    def _locm2_step6(
        AML,
        H_per_sort,
        transitions_per_sort,
        consecutive_transitions_per_sort
    ):
        """
        build transition sets per sort
        """
        """LOCM 2 Algorithm in the original LOCM2 paper"""
        
        # contains Solution Set S for each class.
        transition_sets_per_sort = []

        # for each hole for a class/sort
        for index, holes in enumerate(H_per_sort):
            
            printmd("### Sort.{}".format(index+1))
            
            # S
            transition_set_list = [] #transition_sets_of_a_class, # intially it's empty
            
            if len(holes)==0:
                print("no holes") # S will contain just T_all
            
            if len(holes) > 0: # if there are any holes for a class
                print(str(len(holes)) + " holes")
                for ind, hole in enumerate(holes):
                    printmd("#### Hole " + str(ind + 1) + ": " + str(set(hole)))
                    is_hole_already_covered_flag = False
                    if len(transition_set_list)>0:
                        for s_prime in transition_set_list:
                            if hole.issubset(s_prime):
                                printmd("Hole "+ str(set(hole)) + " is already covered.")
                                is_hole_already_covered_flag = True
                                break
                        
                    # discover a set which includes hole and is well-formed and valid against test data.
                    # if hole is not covered, do BFS with sets of increasing sizes starting with s=hole
                    if not is_hole_already_covered_flag: 
                        h = hole.copy()
                        candidate_sets = []
                        # all subsets of T_all starting from hole's len +1 to T_all-1.
                        for i in range(len(h)+1,len(transitions_per_sort[index])): 
                            subsets = findsubsets(transitions_per_sort[index],i) # all subsets of length i

                            for s in subsets:
                                if h.issubset(s): # if  is subset of s
                                    candidate_sets.append(set(s))
                            
                            s_well_formed_and_valid = False
                            for s in candidate_sets:
                                if len(s)>=i:
                                    printmd("Checking candidate set *" + str(s) + "* of **Sort.{}** for well formedness and Validity".format(index+1))
                                    subset_df = AML[index].loc[list(s),list(s)]
                                    print_table(subset_df)

                                    # checking for well-formedness
                                    well_formed_flag = False
                                    well_formed_flag = check_well_formed(subset_df)
                                    if not well_formed_flag:
                                        print("This subset is NOT well-formed")
                                        
                                    elif well_formed_flag:
                                        print("This subset is well-formed.")
                                        # if well-formed validate across the data E
                                        # to remove inappropriate dead-ends
                                        valid_against_data_flag = False
                                        valid_against_data_flag = check_valid(subset_df, consecutive_transitions_per_sort)
                                        if not valid_against_data_flag:
                                            print("This subset is well-formed but invalid against example data")

                                        if valid_against_data_flag:
                                            print("This subset is valid.")
                                            print("Adding this subset " + str(s) +" to the locm2 transition set.")
                                            if s not in transition_set_list: # do not allow copies.
                                                transition_set_list.append(s)
                                            
                                            print("Hole that is covered now:")
                                            print(list(h))
                                            s_well_formed_and_valid = True
                                            break 
                            if s_well_formed_and_valid:
                                    break
                                            
                                            

            print(transition_set_list)                                    
            #step 7 : remove redundant sets S - {s1}
            ts_copy = transition_set_list.copy()
            for i in range(len(ts_copy)):
                for j in range(len(ts_copy)):
                    if ts_copy[i] < ts_copy[j]: #if subset
                        if ts_copy[i] in transition_set_list:
                            transition_set_list.remove(ts_copy[i])
                    elif ts_copy[i] > ts_copy[j]:
                        if ts_copy[j] in transition_set_list:
                            transition_set_list.remove(ts_copy[j])
            print("\nRemoved redundancy transition set list")
            print(transition_set_list)

            #step-8: include all-transitions machine, even if it is not well-formed.
            transition_set_list.append(set(transitions_per_sort[index])) #fallback
            printmd("#### Final transition set list")
            print(transition_set_list)
            transition_sets_per_sort.append(transition_set_list)
            

        return transition_sets_per_sort


    
    
    @staticmethod
    def _step1(
        obj_traces_overall: ObservedTraceList, sorts: Sorts, transition_sets_per_sort, AML, debug: bool = False
    ) -> Tuple[TSType, APStatePointers, OSType]:
        """Step 1: Create a state machine for each object sort
        Implicitly includes Step 2 (zero analysis) by including the zero-object throughout
        """
        zero_obj = POLOCM.zero_obj
        zero_fsm = FSM(0,0)

        TS_overall = []
        # initialize the state set OS and transition set TS
        OS: OSType = defaultdict(list)
        
        # track pointers mapping A.P to its start and end states
        ap_state_pointers = defaultdict(dict)
        # iterate over each object and its action sequence
        for obj_traces in obj_traces_overall:
            TS: TSType = defaultdict(dict)
            for obj, seq in obj_traces.items():
                if obj != zero_obj:
                    for sort_, transition_sets in enumerate(transition_sets_per_sort):
                        for fsm_no, transitions in enumerate(transition_sets):
                            subseq = [x for x in seq if x in transitions]
                            sort = sorts[obj.name]
                            fsm = FSM(sort, fsm_no)
                            TS[fsm][obj] = subseq
                else:
                    TS[zero_fsm][zero_obj] = seq
                    # state_n = 1
                    # for ap in seq:
                    #     if ap not in ap_state_pointers[zero_fsm]:
                    #         ap_state_pointers[zero_fsm][ap] = StatePointers(state_n, state_n+1)

                    #         OS[zero_fsm].append({state_n})
                    #         OS[zero_fsm].append({state_n + 1})

                    #         state_n+=2

            TS_overall.append(dict(TS))
        if debug:
            print("TS_overall: \n", TS_overall)

        # initialize ap_state_pointers and OS      
        for sort, transition_sets in enumerate(transition_sets_per_sort):
            
            for fsm_no, transitions in enumerate(transition_sets):
                fsm = FSM(sort, fsm_no)

                state_n = 1  # count current (new) state id
                # add the sequence to the transition set
                prev_states: StatePointers = None  # type: ignore
                # iterate over each transition A.P in the sequence
                for ap in transitions:
                    # if the transition has not been seen before for the current sort
                    if ap not in ap_state_pointers[fsm]:
                        ap_state_pointers[fsm][ap] = StatePointers(state_n, state_n + 1)

                        # add the start and end states to the state set as unique states
                        OS[fsm].append({state_n})
                        OS[fsm].append({state_n + 1})

                        state_n += 2
        if debug:
            print('ap_state_pointers: \n', ap_state_pointers)
            print('Initialize OS: \n', OS)

        # unify end - start state for consecutive transitions
        for fsm, ap_states in ap_state_pointers.items():
            for ap, state in ap_states.items():
                
                ts = transition_sets_per_sort[fsm.sort][fsm.index]
                fsm_ts = AML[fsm.sort].loc[list(ts), list(ts)]
                prev_aps = fsm_ts[ap]
                for prev_ap, val in prev_aps.items():
                    current_start, _ = POLOCM._pointer_to_set(OS[fsm], state.start, state.end)
                    if val > 0:
                        prev_state = ap_state_pointers[fsm][prev_ap]
                        _, prev_end = POLOCM._pointer_to_set(OS[fsm], prev_state.start, prev_state.end)
                        if (current_start != prev_end):
                            if OS[fsm][prev_end]:
                                OS[fsm][current_start] = OS[fsm][current_start].union(OS[fsm][prev_end])
                                OS[fsm].pop(prev_end)
                
                # post_aps = fsm_ts.loc[[ap],:].iloc[0,:]
                
                # for post_ap, val in post_aps.items():
                #     _, current_end = LOCM._pointer_to_set(OS[fsm], state.start, state.end)
                #     if val > 0:
                #         post_state = ap_state_pointers[fsm][post_ap]
                #         post_start, _ = LOCM._pointer_to_set(OS[fsm], post_state.start, post_state.end)
                #         if (current_end != post_start):
                #             OS[fsm][current_end] = OS[fsm][current_end].union(OS[fsm][post_start])
                #             OS[fsm].pop(post_start)

        
        # remove the zero-object sort if it only has one state
        if len(OS[zero_fsm]) == 1:
            if debug:
                print('Zero Sort removed!')
            ap_state_pointers[zero_fsm] = {}
            OS[zero_fsm] = []

        if debug:
            print('Final OS: \n', OS)
        return TS_overall, dict(ap_state_pointers), dict(OS)

    @staticmethod
    def _step3(
        TS_overall: List[TSType],
        ap_state_pointers: APStatePointers,
        OS: OSType,
        sorts: Sorts,
        AML,
        debug: bool = False,
    ) -> Hypotheses:
        """Step 3: Induction of parameterised FSMs"""

        zero_obj = POLOCM.zero_obj
        
        # indexed by B.k and C.l for 3.2 matching hypotheses against transitions
        HS: Dict[HSIndex, Set[HSItem]] = defaultdict(set)

        # 3.1: Form hypotheses from state machines
        for TS in TS_overall:
            for fsm, sort_ts in TS.items():
                G = fsm.sort
                # for each O ∈ O_u (not including the zero-object)
                for obj, seq in sort_ts.items():
                    if obj == zero_obj:
                        continue


                    # for each pair of transitions B.k and C.l consecutive for O
                    for B, C in zip(seq, seq[1:]):
                        # skip if B or C only have one parameter, since there is no k' or l' to match on
                        if len(B.action.obj_params) == 1 or len(C.action.obj_params) == 1:
                            continue
                        # skip if B and C are not consistent
                        if AML[fsm.sort].loc[B,C]==0:
                            continue
                        k = B.pos
                        l = C.pos

                        # check each pair B.k' and C.l'
                        for i, Bk_ in enumerate(B.action.obj_params):
                            k_ = i + 1
                            if k_ == k:
                                continue
                            G_ = sorts[Bk_.name]
                            for j, Cl_ in enumerate(C.action.obj_params):
                                l_ = j + 1
                                if l_ == l:
                                    continue

                                # check that B.k' and C.l' are of the same sort
                                if sorts[Cl_.name] == G_:
                                    # check that end(B.P) = start(C.P)
                                    # NOTE: just a sanity check, should never fail
                                    S, S2 = POLOCM._pointer_to_set(
                                        OS[fsm],
                                        ap_state_pointers[fsm][B].end,
                                        ap_state_pointers[fsm][C].start,
                                    )
                                    assert (
                                        S == S2
                                    ), f"end(B.P) != start(C.P)\nB.P: {B}\nC.P: {C}\nseq:{seq}"

                                    # save the hypothesis in the hypothesis set
                                    HS[HSIndex(B, k, C, l)].add(
                                        HSItem(S, k_, l_, G, G_, supported=False, fsm=fsm)
                                    )
                                    if debug:
                                        print("Adding Hypo:")
                                        pprint(Hypothesis(S,B,k,k_,C,l,l_,G,G_,fsm))

        # 3.2: Test hypotheses against sequence
        for TS in TS_overall:
            for fsm, sort_ts in TS.items():
                # for each O ∈ O_u (not including the zero-object)
                for obj, seq in sort_ts.items():
                    if obj == zero_obj:
                        continue

                    
                    # for each pair of transitions Ap.m and Aq.n consecutive for O
                    for Ap, Aq in zip(seq, seq[1:]):
                        m = Ap.pos
                        n = Aq.pos
                        # Check if we have a hypothesis matching Ap=B, m=k, Aq=C, n=l
                        BkCl = HSIndex(Ap, m, Aq, n)
                        if BkCl in HS:
                            # check each matching hypothesis
                            for H in HS[BkCl].copy():
                                # if Op,k' = Oq,l' then mark the hypothesis as supported
                                if (
                                    Ap.action.obj_params[H.k_ - 1]
                                    == Aq.action.obj_params[H.l_ - 1]
                                ):
                                    H.supported = True
                                else:  # otherwise remove the hypothesis
                                    HS[BkCl].remove(H)

        # Remove any unsupported hypotheses (but yet undisputed)
        for hind, hs in HS.copy().items():
            for h in hs:
                if not h.supported:
                    hs.remove(h)
            if len(hs) == 0:
                del HS[hind]

        # Converts HS {HSIndex: HSItem} to a mapping of hypothesis for states of a sort {sort: {state: Hypothesis}}
        converted_HS = Hypothesis.from_dict(HS)
        if debug:
            print('Learned HS:')
            for fsm, Hyps in converted_HS.items():
                print(fsm)
                for state, hyp in Hyps.items():
                    pprint(hyp)
        return converted_HS

    @staticmethod
    def _step4(
        HS: Dict[FSM, Dict[int, Set[Hypothesis]]], debug: bool = False
    ) -> Bindings:
        """Step 4: Creation and merging of state parameters"""

        # bindings = {fsm: {state: [(hypothesis, state param)]}}
        bindings: Bindings = defaultdict(dict)
        for fsm, hs_fsm in HS.items():
            for state, hs_fsm_state in hs_fsm.items():
                # state_bindings = {hypothesis (h): state param (v)}
                state_bindings: Dict[Hypothesis, int] = {}

                # state_params = [set(v)]; params in the same set are the same
                state_params: List[Set[int]] = []

                # state_param_pointers = {v: P}; maps state param to the state_params set index
                # i.e. map hypothesis state param v -> actual state param P
                state_param_pointers: Dict[int, int] = {}

                # for each hypothesis h,
                hs_fsm_state = list(hs_fsm_state)
                for v, h in enumerate(hs_fsm_state):
                    # add the <h, v> binding pair
                    state_bindings[h] = v
                    # add a param v as a unique state parameter
                    state_params.append({v})
                    state_param_pointers[v] = v

                # for each (unordered) pair of hypotheses h1, h2
                for i, h1 in enumerate(hs_fsm_state):
                    for h2 in hs_fsm_state[i + 1 :]:
                        # check if hypothesis parameters (v1 & v2) need to be unified
                        if (
                            (h1.B == h2.B and h1.k == h2.k and h1.k_ == h2.k_)
                            or
                            (h1.C == h2.C and h1.l == h2.l and h1.l_ == h2.l_)  # fmt: skip
                        ):
                            v1 = state_bindings[h1]
                            v2 = state_bindings[h2]

                            # get the parameter sets P1, P2 that v1, v2 belong to
                            P1, P2 = POLOCM._pointer_to_set(state_params, v1, v2)

                            if P1 != P2:
                                # merge P1 and P2
                                state_params[P1] = state_params[P1].union(
                                    state_params[P2]
                                )
                                state_params.pop(P2)
                                state_param_pointers[v2] = P1

                # add state bindings for the sort to the output bindings
                # replacing hypothesis params with actual state params
                bindings[fsm][state] = [
                    Binding(h, POLOCM._pointer_to_set(state_params, v)[0])
                    for h, v in state_bindings.items()
                ]
        if debug:
            pprint(bindings)
        return dict(bindings)

    @staticmethod
    def _step5(
        HS: Dict[FSM, Dict[int, Set[Hypothesis]]],
        bindings: Bindings,
        debug: bool = False,
    ) -> Bindings:
        """Step 5: Removing parameter flaws"""

        # check each bindings[G][S] -> (h, P)
        for fsm, hs_fsm in HS.items():
            for state in hs_fsm:
                # track all the h.Bs that occur in bindings[G][S]
                all_hB = set()
                # track the set of h.B that set parameter P
                sets_P = defaultdict(set)
                for h, P in bindings[fsm][state]:
                    sets_P[P].add(h.B)
                    all_hB.add(h.B)

                # for each P, check if there is a transition h.B that never sets parameter P
                # i.e. if sets_P[P] != all_hB
                for P, setby in sets_P.items():
                    if not setby == all_hB:  # P is a flawed parameter
                        # remove all bindings referencing P
                        for h, P_ in bindings[fsm][state].copy():
                            if P_ == P:
                                bindings[fsm][state].remove(Binding(h, P_))
                        if len(bindings[fsm][state]) == 0:
                            del bindings[fsm][state]

        for k, v in bindings.copy().items():
            if not v:
                del bindings[k]

        return bindings

    @staticmethod
    def get_state_machines(
        ap_state_pointers: APStatePointers,
        OS: OSType,
        bindings: Optional[Bindings] = None,
    ):
        from graphviz import Digraph

        state_machines = []
        for (fsm, trans), states in zip(ap_state_pointers.items(), OS.values()):
            graph = Digraph(f"LOCM-step1-{fsm}")
            for state in range(len(states)):
                label = f"state{state}"
                if (
                    bindings is not None
                    and fsm in bindings
                    and state in bindings[fsm]
                ):
                    label += f"\n["
                    params = []
                    for binding in bindings[fsm][state]:
                        params.append(f"{binding.hypothesis.G_}")
                    label += f",".join(params)
                    label += f"]"
                graph.node(str(state), label=label, shape="oval")
            for ap, apstate in trans.items():
                start_idx, end_idx = POLOCM._pointer_to_set(
                    states, apstate.start, apstate.end
                )
                graph.edge(
                    str(start_idx), str(end_idx), label=f"{ap.action.name}.{ap.pos}"
                )

            state_machines.append(graph)

        return state_machines

    @staticmethod
    def _step7(
        OS: OSType,
        ap_state_pointers: APStatePointers,
        sorts: Sorts,
        bindings: Bindings,
        statics: Statics,
        debug: bool = False,
    ) -> Tuple[Set[LearnedLiftedFluent], Set[LearnedLiftedAction]]:
        """Step 7: Formation of PDDL action schema
        Implicitly includes Step 6 (statics) by including statics as an argument
        and adding to the relevant actions while being constructed.
        """

        shift = 0
        # delete zero-object if it's state machine was discarded
        zero_fsm = FSM(0,0)
        if not OS[zero_fsm]:
            del OS[zero_fsm]
            del ap_state_pointers[zero_fsm]
            shift = 1

        if debug:

            print("bindings:")
            pprint(bindings)
            print()

        bound_param_sorts = {
            fsm: {
                state: [
                    binding.hypothesis.G_
                    for binding in bindings.get(fsm, {}).get(state, [])
                ]
                for state in range(len(states))
            }
            for fsm, states in OS.items()
        }

        actions = {}
        fluents = defaultdict(dict)

        all_aps: Dict[str, Set[AP]] = defaultdict(set)
        for aps in ap_state_pointers.values():
            for ap in aps:
                all_aps[ap.action.name].add(ap)
        for action, aps in all_aps.items():
            param_sorts = [ap for ap in aps]
            param_sorts.sort(key=lambda ap: ap.pos)
            actions[action] = LearnedLiftedAction(
                action, [f"sort{s.sort}" for s in param_sorts]
            )

        @dataclass
        class TemplateFluent:
            name: str
            param_sorts: List[str]

            def __hash__(self) -> int:
                return hash(self.name + "".join(self.param_sorts))

        for fsm, state_bindings in bound_param_sorts.items():
            for state, bound_sorts in state_bindings.items():
                fluents[fsm][state] = TemplateFluent(
                    f"fsm{fsm}_state{state}",
                    [f"sort{fsm.sort}"]+[f"sort{s}" for s in bound_sorts],
                )

        for (fsm, aps), states in zip(ap_state_pointers.items(), OS.values()):
            for ap, pointers in aps.items():
                start_state, end_state = POLOCM._pointer_to_set(
                    states, pointers.start, pointers.end
                )

                # preconditions += fluent for origin state
                start_fluent_temp = fluents[fsm][start_state]

                bound_param_inds = []

                # for each bindings on the start state (if there are any)
                # then add each binding.hypothesis.l_
                if fsm in bindings and start_state in bindings[fsm]:
                    bound_param_inds = [
                        b.hypothesis.l_- shift  for b in bindings[fsm][start_state]
                    ]

                start_fluent = LearnedLiftedFluent(
                    start_fluent_temp.name,
                    start_fluent_temp.param_sorts,
                    [ap.pos-shift] + bound_param_inds,
                )
                fluents[fsm][start_state] = start_fluent
                actions[ap.action.name].update_precond(start_fluent)

                if start_state != end_state:
                    # del += fluent for origin state
                    actions[ap.action.name].update_delete(start_fluent)

                    # add += fluent for destination state
                    end_fluent_temp = fluents[fsm][end_state]
                    bound_param_inds = []
                    if fsm in bindings and end_state in bindings[fsm]:
                        bound_param_inds = [
                            b.hypothesis.l_ -shift  for b in bindings[fsm][end_state]
                        ]
                    end_fluent = LearnedLiftedFluent(
                        end_fluent_temp.name,
                        end_fluent_temp.param_sorts,
                        [ap.pos-shift] + bound_param_inds,
                    )
                    fluents[fsm][end_state] = end_fluent
                    actions[ap.action.name].update_add(end_fluent)

        fluents = set(fluent for fsm in fluents.values() for fluent in fsm.values())
        actions = set(actions.values())

        # Step 6: Extraction of static preconditions
        for action in actions:
            if action.name in statics:
                for static in statics[action.name]:
                    action.update_precond(static)

        if debug:
            print('fluents:')
            pprint(fluents)
            print()
            print("actions:")
            pprint(actions)
            print()

        return fluents, actions
