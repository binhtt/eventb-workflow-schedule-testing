import collections as c
import concurrent.futures as cf
import csv
import itertools as it
import json
import os
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'code'))
from eventb import Model
from experiment import MODEL_PATH
from runtime import MUTANTS, Service
from scheduling import build_suite, extract_objectives, fixture, synthesize
from analyse import eligible

ROOT = Path(__file__).resolve().parents[2]
PLAN = json.loads((ROOT / 'plan.json').read_text())

def replay(order, size, capacity, mutant, model, operations):
    service = Service(size, capacity, mutant)
    state = model.initialise(size, capacity)
    first_c = first_q = None
    try:
        if service.snapshot() != state or model.errors(state):
            first_c = 0
        for k, (request, name, hook) in enumerate(order, 1):
            op = operations[request, name]
            if hook == 'probe':
                before = service.snapshot()
                service.probe(op)
                if first_c is None and service.snapshot() != before:
                    first_c = k
                continue
            event = model.events[op.action]
            enabled = event.enabled(state, op.parameters)
            if enabled:
                state = event.apply(state, op.parameters)
            accepted, observations = service.apply(op)
            actual = service.snapshot()
            if first_c is None and (enabled != accepted or actual != state or
                                    model.errors(actual) or (not accepted and observations)):
                first_c = k
            if service.audit(observations) and first_q is None:
                first_q = k
        return first_c, first_q
    finally:
        service.close()

def run(task):
    size, capacity, method, seed = task
    model = Model(MODEL_PATH)
    operations, predecessors = fixture(size)
    suite, stats = build_suite(method, size, capacity, seed, 16, model)
    assert len(suite) == 16
    prefix = next((k for k, hooks in enumerate(zip(*suite)) if len(set(hooks)) > 1), len(suite[0]))
    assert all(replay(order,size,capacity,None,model,operations)==(None,None) for order in suite)
    rows = []
    for mutant in MUTANTS:
        first = [None] * 3
        for i, order in enumerate(suite, 1):
            conf, audit = replay(order,size,capacity,mutant,model,operations)
            for j, found in enumerate((conf is not None, audit is not None, conf is not None or audit is not None)):
                if found and first[j] is None:
                    first[j] = i
        rows.append(dict(requests=size,capacity=capacity,method=method,seed=seed,mutant=mutant,
                         conformance=first[0],audit=first[1],combined=first[2]))
    coverage = dict(requests=size,capacity=capacity,method=method,seed=seed,
                    distinct=len(set(map(tuple,suite))),common_prefix=prefix,**stats)
    if method == 'model_conflicts':
        goals = extract_objectives(model,operations,predecessors)
        rng = random.Random(seed)
        rng.shuffle(goals)
        targeted, seen_feasible, generated = [], [], []
        for goal in goals:
            order = synthesize(goal,operations,predecessors,model,size,capacity,rng)
            if order is None:
                continue
            pair = [goal['a'],goal['b']]
            seen_feasible.append(pair)
            if len(targeted)<16:
                targeted.append(pair)
                generated.append(order)
        assert generated == suite[:len(generated)]
        coverage.update(targeted_pairs=targeted,feasible_sample=seen_feasible)
    return rows,coverage

if __name__ == '__main__':
    tasks = [(n,k,m,s) for n,k in PLAN['configurations'] for m in PLAN['methods'] for s in range(PLAN['seeds'])]
    rows,coverage = [],[]
    with cf.ProcessPoolExecutor(max_workers=min(12,os.cpu_count() or 1)) as pool:
        for a,b in pool.map(run,tasks,chunksize=3):
            rows.extend(a)
            coverage.append(b)
            if len(coverage)%50==0:print(len(coverage),flush=True)
    with (ROOT/'results/trials.csv').open() as f:
        original=list(csv.DictReader(f))
    assert len(original)==len(rows)
    for a,b in zip(original,rows):
        assert all(str(b[k])==a[k] for k in ('requests','capacity','method','seed','mutant'))
        assert (str(b['audit']) if b['audit'] else '')==a['first_detection']
    output=ROOT/'outputs/supplemental'
    output.mkdir(parents=True, exist_ok=True)
    for name, data in [('ablation',rows),('coverage',coverage)]:
        (output/f'{name}.json').write_text(json.dumps(data,indent=2))
