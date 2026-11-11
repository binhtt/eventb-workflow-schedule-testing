"""Paired standalone timing, with method order shuffled in each repetition."""
from pathlib import Path
import random
import statistics
import time
from analyse import save
from eventb import Model
from experiment import MODEL_PATH,replay
from scheduling import build_suite

def main():
    model=Model(MODEL_PATH)
    methods=['nominal','random','model_conflicts','canonical_independence']
    rows=[]
    for requests,capacity in ((2,1),(4,2),(8,3)):
        for repetition in range(30):
            order=methods.copy(); random.Random(30000+repetition).shuffle(order)
            for method in order:
                start=time.perf_counter()
                suite,_=build_suite(method,requests,capacity,1000+repetition,16,model)
                generation=time.perf_counter()-start
                start=time.perf_counter()
                for schedule in suite:
                    failures,_,_=replay(schedule,requests,capacity,None,model,conformance=True)
                    assert not failures
                execution=time.perf_counter()-start
                rows.append({'requests':requests,'capacity':capacity,'method':method,
                             'repetition':repetition,'generation_ms':1000*generation,
                             'clean_suite_replay_ms':1000*execution,
                             'end_to_end_suite_ms':1000*(generation+execution)})
    save('standalone_timing.csv',rows)
    summary=[]
    for requests,capacity in ((2,1),(4,2),(8,3)):
        for method in methods:
            group=[r for r in rows if r['requests']==requests and r['method']==method]
            summary.append({'requests':requests,'capacity':capacity,'method':method,
                            'median_generation_ms':statistics.median(r['generation_ms'] for r in group),
                            'median_clean_suite_replay_ms':statistics.median(r['clean_suite_replay_ms'] for r in group),
                            'median_end_to_end_suite_ms':statistics.median(r['end_to_end_suite_ms'] for r in group)})
    save('standalone_timing_summary.csv',summary)
    for row in summary: print(row)

if __name__=='__main__': main()
