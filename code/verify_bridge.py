"""Check all schedule suites against the normalized proved source."""
from pathlib import Path
import hashlib
import json
from eventb import Model
from proof_bridge import load_proved,assert_same_core
from scheduling import build_suite
from experiment import MODEL_PATH,ROOT

def main():
    source=Model(MODEL_PATH)
    proved,transformations=load_proved(ROOT/'proof/SharedWorkflow/Resource.bum')
    assert_same_core(source,proved)
    assert (ROOT/'proof/SharedWorkflow/Pool.buc').read_bytes()==(ROOT/'model/SharedWorkflow/Pool.buc').read_bytes()
    plan=json.loads((ROOT/'plan.json').read_text())
    suites=schedules=0
    digest=hashlib.sha256()
    for size,capacity in plan['configurations']:
        for method in plan['methods']:
            for seed in range(plan['seeds']):
                first,stats1=build_suite(method,size,capacity,seed,16,source)
                second,stats2=build_suite(method,size,capacity,seed,16,proved)
                assert first==second and stats1==stats2
                suites+=1; schedules+=len(first)
                digest.update(json.dumps(first).encode())
    result={'equivalent_core':True,'same_context':True,'identical_suites':suites,
            'identical_schedules':schedules,'schedule_digest':digest.hexdigest(),
            'transformations':transformations}
    (ROOT/'results/proof_bridge.json').write_text(json.dumps(result,indent=2))
    print(result)

if __name__=='__main__': main()
