import csv
import json
from ablation_review import PLAN, ROOT, eligible
import statistics as st
p=ROOT/'outputs/supplemental'
a=json.loads((p/'ablation.json').read_text())
g=json.loads((p/'coverage.json').read_text())
modes=('conformance','audit','combined')
def counts(rows,budget):
    return [sum(r[k] is not None and r[k]<=budget for r in rows) for k in modes]
for m in PLAN['methods']:
    z=[r for r in a if r['method']==m]
    q=[r for r in z if eligible(r,PLAN)]
    print(m,'raw',counts(z,16),'eligible',[(b,counts(q,b)) for b in (1,4,8,16)])
    print('paired',[(b,sum(r['combined'] is not None and r['combined']<=b and (r['audit'] is None or r['audit']>b) for r in q),sum(r['combined'] is not None and r['combined']<=b and (r['conformance'] is None or r['conformance']>b) for r in q)) for b in (1,4,16)])
for n,k in PLAN['configurations']:
    for m in ('model_conflicts','canonical_independence','random'):
        z=[r for r in g if (r['requests'],r['capacity'],r['method'])==(n,k,m)]
        print(n,k,m,'distinct',min(r['distinct'] for r in z),max(r['distinct'] for r in z),'prefix',min(r['common_prefix'] for r in z),st.median(r['common_prefix'] for r in z),max(r['common_prefix'] for r in z))
        if m=='model_conflicts':
            for key in ('candidate_objectives','attempted_objectives','feasible_objectives'):
                print(key,min(r[key] for r in z),st.median(r[key] for r in z),max(r[key] for r in z))
            for key in ('feasible_sample','targeted_pairs'):
                print(key,'min median max',min(len(r[key]) for r in z),st.median(len(r[key]) for r in z),max(len(r[key]) for r in z),'union',len({tuple(map(tuple,pair)) for r in z for pair in r[key]}))
t=list(csv.DictReader((p/'timing.csv').open()))
keys = ('requests', 'capacity', 'seed', 'method', 'mutant')
by_trial = {tuple(str(row[k]) for k in keys): row for row in a}
for r in t:
    row = by_trial[tuple(r[k] for k in keys)]
    assert str(row['audit'] or '') == r['schedule']
for n,k in PLAN['configurations']:
    for m in ('model_conflicts','random'):
        z=[r for r in t if (int(r['requests']),int(r['capacity']),r['method'])==(n,k,m)]
        print(n,k,m,'time curve',[(b,sum(bool(r['schedule']) and float(r['elapsed_ms'])<=b for r in z),len(z)) for b in (10,25,50,100,200)])
