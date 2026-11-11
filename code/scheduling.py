"""Model-derived guard interference objectives and declared-order baselines."""
from dataclasses import dataclass
from itertools import combinations
import random
from eventb import Model

@dataclass(frozen=True)
class Operation:
    request:int
    name:str
    action:str
    epoch:int=0
    @property
    def identity(self):
        return (self.request,self.name)
    @property
    def parameters(self):
        return {'r':self.request,'v':self.epoch}

# Adapter metadata. It binds implementation hooks to abstract event schemas
# and declares protocol precedence, independently of the mutation suite.
ADAPTER = {
    'reserve':('Reserve',()),
    'retry_reserve':('Reserve',()),
    'execute':('Execute',('reserve',)),
    'retry_execute':('Execute',('reserve',)),
    'handoff':('Transfer',('reserve',)),
    'ack':('Acknowledge',('execute',)),
    'release':('Release',('execute',)),
    'expiry':('Expire',('reserve',)),
}

def fixture(size):
    operations=[Operation(r,name,action) for r in range(size)
                for name,(action,_) in ADAPTER.items()]
    by_id={op.identity:op for op in operations}
    predecessors={}
    for operation in operations:
        request,name=operation.identity
        predecessors[operation.identity+('probe',)]={
            (request,pred,'apply') for pred in ADAPTER[name][1]}
        predecessors[operation.identity+('apply',)]={operation.identity+('probe',)}
    return by_id,predecessors

def random_order(predecessors,rng):
    done=set(); order=[]
    while len(done)<len(predecessors):
        enabled=[event for event,pred in predecessors.items() if event not in done and pred<=done]
        chosen=rng.choice(enabled); done.add(chosen); order.append(chosen)
    return order

def ancestors(event,predecessors):
    found=set(); frontier=list(predecessors[event])
    while frontier:
        item=frontier.pop()
        if item not in found:
            found.add(item); frontier.extend(predecessors[item])
    return found

def guard_accesses(expression,variables,request):
    if (expression.op in ('∈','∉') and expression.args[0].op=='name'
        and expression.args[0].args==('r',) and expression.args[1].op=='name'
        and expression.args[1].args[0] in variables):
        return {(expression.args[1].args[0],request)}
    if expression.op=='name':
        return {(expression.args[0],None)} if expression.args[0] in variables else set()
    return set().union(*(guard_accesses(arg,variables,request)
                         for arg in expression.args if hasattr(arg,'op')))

def write_accesses(event,request):
    accesses=set()
    for variable,expression in event.assignments.items():
        local=(expression.op in ('∪','∖') and expression.args[0].op=='name'
               and expression.args[0].args==(variable,) and expression.args[1].op=='set'
               and len(expression.args[1].args)==1
               and expression.args[1].args[0].op=='name'
               and expression.args[1].args[0].args==('r',))
        accesses.add((variable,request if local else None))
    return accesses

def overlaps(first,second):
    return first[0]==second[0] and (first[1] is None or second[1] is None or first[1]==second[1])

def extract_objectives(model,operations,predecessors):
    goals=[]
    for first,second in combinations(operations.values(),2):
        a,b=model.events[first.action],model.events[second.action]
        conflicts=[]
        for writer,reader,writer_op,reader_op in ((a,b,first,second),(b,a,second,first)):
            reads=set().union(*(guard_accesses(expr,model.variables,reader_op.request)
                                    for expr in reader.guards.values()))
            for write in write_accesses(writer,writer_op.request):
                conflicts.extend(write[0] for read in reads if overlaps(write,read))
        if not conflicts: continue
        ap,bp=first.identity+('probe',),second.identity+('probe',)
        aa,ba=first.identity+('apply',),second.identity+('apply',)
        prefix=ancestors(ap,predecessors)|ancestors(bp,predecessors)
        if aa in prefix or ba in prefix: continue
        goals.append({'a':first.identity,'b':second.identity,'variables':sorted(set(conflicts)),
                      'prefix':prefix})
    return goals

def synthesize(goal,operations,predecessors,model,size,capacity,rng):
    """Find a legal ancestor prefix with both abstract guards enabled."""
    done=set(); order=[]; state=model.initialise(size,capacity)
    prefix=goal['prefix']
    while done!=prefix:
        enabled=[event for event in prefix-done if predecessors[event]<=done]
        if not enabled: return None
        event=rng.choice(sorted(enabled)); order.append(event); done.add(event)
        if event[2]=='apply':
            operation=operations[event[:2]]; abstract=model.events[operation.action]
            if abstract.enabled(state,operation.parameters):
                state=abstract.apply(state,operation.parameters)
    a,b=operations[goal['a']],operations[goal['b']]
    if not all(model.events[operation.action].enabled(state,operation.parameters) for operation in (a,b)):
        return None
    # Two directions are tested through a seeded orientation.
    if rng.randrange(2): a,b=b,a
    for event in (a.identity+('probe',),b.identity+('probe',),
                  b.identity+('apply',),a.identity+('apply',)):
        assert event not in done and predecessors[event]<=done
        done.add(event); order.append(event)
    while len(done)<len(predecessors):
        enabled=[event for event,pred in predecessors.items() if event not in done and pred<=done]
        event=rng.choice(enabled); done.add(event); order.append(event)
    return order

def sleep_orders(predecessors,rng,limit):
    """Sleep-set DFS; only probe/probe pairs are declared independent.

    Apply hooks remain dependent across all requests. No broad DPOR claim.
    """
    ranking=list(predecessors); rng.shuffle(ranking)
    outputs=0
    def visit(done,order,sleep):
        nonlocal outputs
        if outputs>=limit: return
        if len(done)==len(predecessors):
            outputs+=1; yield list(order); return
        enabled=[event for event in ranking if event not in done and predecessors[event]<=done]
        local_sleep=set(sleep)
        for event in enabled:
            if event in local_sleep: continue
            independent=lambda other: event[2]=='probe' and other[2]=='probe'
            next_sleep={other for other in local_sleep if independent(other)}
            yield from visit(done|{event},order+[event],next_sleep)
            local_sleep.add(event)
            if outputs>=limit: return
    yield from visit(set(),[],set())

def build_suite(method,size,capacity,seed,budget,model):
    rng=random.Random(seed)
    operations,predecessors=fixture(size)
    stats={'candidate_objectives':0,'attempted_objectives':0,'feasible_objectives':0}
    if method=='nominal':
        order=[]
        for r in range(size):
            for name in ADAPTER:
                order.extend(((r,name,'probe'),(r,name,'apply')))
        return [order]*budget,stats
    if method=='random':
        return [random_order(predecessors,rng) for _ in range(budget)],stats
    if method=='canonical_independence':
        return list(sleep_orders(predecessors,rng,budget)),stats
    if method!='model_conflicts': raise ValueError(method)
    goals=extract_objectives(model,operations,predecessors)
    stats['candidate_objectives']=len(goals); rng.shuffle(goals)
    suite=[]
    for goal in goals:
        stats['attempted_objectives']+=1
        order=synthesize(goal,operations,predecessors,model,size,capacity,rng)
        if order is None: continue
        stats['feasible_objectives']+=1; suite.append(order)
        if len(suite)==budget: break
    while len(suite)<budget:
        suite.append(random_order(predecessors,rng))
    return suite,stats
