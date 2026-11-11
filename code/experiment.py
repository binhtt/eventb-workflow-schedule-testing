"""Run paired, fixed-budget scheduling experiments on a separate SQL service."""
from collections import Counter,defaultdict
from pathlib import Path
import csv
import hashlib
import json
import platform
import statistics
import time

from eventb import Model
from scheduling import build_suite,fixture
from runtime import Service,MUTANTS

ROOT=Path(__file__).resolve().parents[1]
MODEL_PATH=ROOT/'model/SharedWorkflow/Resource.bum'

def replay(order,size,capacity,mutant,model,conformance=False,trace=False):
    operations,predecessors=fixture(size)
    service=Service(size,capacity,mutant)
    state=model.initialise(size,capacity)
    failures=set(); log=[]; done=set(); mismatch=None
    try:
        for request,name,hook in order:
            identity=(request,name,hook)
            assert identity not in done and predecessors[identity]<=done
            done.add(identity)
            operation=operations[request,name]
            observations=[]
            if hook=='probe':
                service.probe(operation)
            else:
                if conformance:
                    event=model.events[operation.action]
                    enabled=event.enabled(state,operation.parameters)
                    expected=event.apply(state,operation.parameters) if enabled else state
                accepted,observations=service.apply(operation)
                current=service.snapshot() if conformance else None
                if conformance:
                    errors=model.errors(current)
                    if enabled!=accepted or current!=expected or errors:
                        mismatch={'hook':identity,'accepted':accepted,'enabled':enabled,'invariants':errors}
                        if not mutant: raise AssertionError(mismatch)
                    state=expected
                failures.update(service.audit(observations))
            if trace:
                snapshot={key:sorted(value) if isinstance(value,frozenset) else value
                          for key,value in service.snapshot().items()}
                log.append({'hook':identity,'observations':observations,
                            'snapshot':snapshot,'failures':sorted(failures)})
        assert len(done)==len(predecessors)
    finally:
        service.close()
    return sorted(failures),log,mismatch

def write_csv(path,rows):
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

def main():
    plan=json.loads((ROOT/'plan.json').read_text())
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--proved-model',type=Path)
    arguments=parser.parse_args()
    model=Model(MODEL_PATH)
    if arguments.proved_model:
        from proof_bridge import load_proved,assert_same_core
        proved,_=load_proved(arguments.proved_model)
        assert_same_core(model,proved)
        model=proved
    results=ROOT/'results'; results.mkdir(exist_ok=True)
    trials=[]; costs=[]; witnesses={}
    configs=plan['configurations']; budget=max(plan['budgets'])
    started=time.perf_counter()
    for size,capacity in configs:
        for method in plan['methods']:
            for seed in range(plan['seeds']):
                begin=time.perf_counter()
                suite,stats=build_suite(method,size,capacity,seed,budget,model)
                generation=time.perf_counter()-begin
                assert len(suite)==budget
                first={}
                replay_begin=time.perf_counter()
                for execution,order in enumerate(suite,1):
                    clean,_,_=replay(order,size,capacity,None,model,conformance=True)
                    assert not clean, (method,size,capacity,seed,execution,clean)
                    # Every mutant gets the full budget, even after detection.
                    for mutant in MUTANTS:
                        failures,_,_=replay(order,size,capacity,mutant,model)
                        if failures:
                            first.setdefault(mutant,execution)
                            key=(size,capacity,method,mutant)
                            witnesses.setdefault(key,(seed,order,failures))
                replay_seconds=time.perf_counter()-replay_begin
                for mutant in MUTANTS:
                    trials.append({'requests':size,'capacity':capacity,'method':method,
                                   'seed':seed,'mutant':mutant,'first_detection':first.get(mutant,'')})
                costs.append({'requests':size,'capacity':capacity,'method':method,'seed':seed,
                              'generation_seconds':generation,'replay_seconds':replay_seconds,
                              **stats})
            print(size,capacity,method,'completed',flush=True)
            write_csv(results/'trials.csv',trials); write_csv(results/'costs.csv',costs)
    traces=[]
    for (size,capacity,method,mutant),(seed,order,failures) in witnesses.items():
        actual,log,_=replay(order,size,capacity,mutant,model,trace=True)
        assert actual==failures
        traces.append({'requests':size,'capacity':capacity,'method':method,'mutant':mutant,
                       'seed':seed,'schedule':order,'failures':failures,'log':log})
    (results/'witnesses.json').write_text(json.dumps(traces,indent=2))
    summary={'configurations':configs,'seed_count':plan['seeds'],'budget':budget,
             'methods':plan['methods'],'clean_replays':len(costs)*budget,
             'mutant_replays':len(costs)*budget*len(MUTANTS),
             'elapsed_seconds':time.perf_counter()-started,
             'python':platform.python_version(),'platform':platform.platform(),
             'model_sha256':hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()}
    (results/'run_summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
