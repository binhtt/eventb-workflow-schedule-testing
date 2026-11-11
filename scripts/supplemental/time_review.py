import csv
import random
import time

from ablation_review import PLAN, ROOT, Model, MODEL_PATH, build_suite, eligible
from experiment import replay

model = Model(MODEL_PATH)
rng = random.Random(20261110)
timings = []
for size, capacity in PLAN['configurations']:
    mutants = [m for m in PLAN['evaluation_faults'] if eligible({'mutant':m,'capacity':capacity},PLAN)]
    for seed in range(PLAN['seeds']):
        methods = ['random','model_conflicts']
        rng.shuffle(methods)
        for method in methods:
            start = time.perf_counter()
            suite,_ = build_suite(method,size,capacity,seed,16,model)
            generation = time.perf_counter()-start
            for mutant in mutants:
                start = time.perf_counter()
                found = None
                for index,order in enumerate(suite,1):
                    failures,_,_ = replay(order,size,capacity,mutant,model)
                    if failures:
                        found = index
                        break
                elapsed = time.perf_counter()-start
                timings.append(dict(requests=size,capacity=capacity,seed=seed,method=method,mutant=mutant,
                                    schedule=found,generation_ms=1000*generation,
                                    elapsed_ms=1000*(generation+elapsed)))
    print(size,capacity,flush=True)
output = ROOT/'outputs/supplemental'
output.mkdir(parents=True, exist_ok=True)
with (output/'timing.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(timings[0]))
    writer.writeheader()
    writer.writerows(timings)
