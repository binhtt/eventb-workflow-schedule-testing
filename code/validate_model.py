"""Exhaustively compare the XML model with the clean SQL implementation."""
from collections import deque
from pathlib import Path
import json
import time
from eventb import Model
from scheduling import Operation
from runtime import Service
from experiment import MODEL_PATH

def state_key(state):
    return tuple((key,tuple(sorted(value)) if isinstance(value,frozenset) else value)
                 for key,value in sorted(state.items()))

def load_service(state,size,capacity):
    service=Service(size,capacity)
    service.db.execute('UPDATE pool SET available=?',(state['free'],))
    for variable,table in (('held','leases'),('closed','terminated'),('moved','handovers'),
                           ('effected','effects'),('acked','acknowledgements')):
        service.db.executemany(f'INSERT INTO {table} VALUES (?)',((r,) for r in state[variable]))
    service.db.commit()
    return service

def explore(size,capacity,limit=100000):
    model=Model(MODEL_PATH)
    initial=model.initialise(size,capacity)
    queue=deque([initial]); visited={state_key(initial)}
    enabled=disabled=edges=0
    begin=time.perf_counter()
    while queue:
        state=queue.popleft()
        assert not model.errors(state)
        for event in model.events.values():
            if event.name=='INITIALISATION': continue
            epochs=(0,1) if event.name in ('Execute','Acknowledge') else (0,)
            for request in range(size):
                for epoch in epochs:
                    operation=Operation(request,event.name,event.name,epoch)
                    allowed=event.enabled(state,operation.parameters)
                    expected=event.apply(state,operation.parameters) if allowed else state
                    service=load_service(state,size,capacity)
                    service.probe(operation)
                    accepted,observations=service.apply(operation)
                    assert accepted==allowed
                    assert service.snapshot()==expected,(event.name,state,expected,service.snapshot())
                    assert not service.audit(observations)
                    service.close()
                    if allowed:
                        enabled+=1
                        assert not model.errors(expected)
                        key=state_key(expected)
                        if key not in visited:
                            visited.add(key)
                            if len(visited)>limit: raise RuntimeError('State bound exceeded')
                            queue.append(expected)
                    else: disabled+=1
                    edges+=1
    return {'requests':size,'capacity':capacity,'states':len(visited),
            'enabled_transitions':enabled,'rejected_attempts':disabled,
            'all_attempts':edges,'complete':True,'seconds':time.perf_counter()-begin}

def main():
    results=[]
    for config in ((1,1),(2,1),(3,2)):
        row=explore(*config); results.append(row); print(row,flush=True)
    (Path(__file__).resolve().parents[1] / 'results').joinpath('model_conformance.json').write_text(json.dumps(results,indent=2))

if __name__=='__main__': main()
