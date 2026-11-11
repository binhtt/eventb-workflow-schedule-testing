"""Analyse all results with explicit nominal and feasibility qualification."""
from collections import defaultdict
from pathlib import Path
import csv
import json
import random
import statistics

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'results'

def read(name):
    return list(csv.DictReader((RESULTS/name).open()))

def save(name,rows):
    with (RESULTS/name).open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

def found(row,budget):
    return bool(row['first_detection']) and int(row['first_detection'])<=budget

def eligible(row,plan):
    if row['mutant'] not in plan['evaluation_faults']: return False
    if row['mutant'] in ('transfer_credit','ack_old_epoch'): return False
    # This mutant changes a victim only when another request holds a lease.
    # Capacity one makes that branch unreachable under the correct protocol.
    return not (row['mutant']=='release_wrong_key' and int(row['capacity'])==1)

def percentile(values,p):
    values=sorted(values)
    return values[round(p*(len(values)-1))]

def main():
    plan=json.loads((ROOT/'plan.json').read_text()); rows=read('trials.csv')
    table=[]
    for size,capacity in plan['configurations']:
        for method in plan['methods']:
            subset=[row for row in rows if int(row['requests'])==size and int(row['capacity'])==capacity
                    and row['method']==method and eligible(row,plan)]
            for budget in plan['budgets']:
                count=sum(found(row,budget) for row in subset)
                table.append({'requests':size,'capacity':capacity,'method':method,'budget':budget,
                              'detected':count,'eligible_trials':len(subset),
                              'percent':100*count/len(subset)})
    save('qualified_summary.csv',table)
    per_fault=[]
    for size,capacity in plan['configurations']:
        for mutant in plan['development_faults']+plan['evaluation_faults']:
            for method in plan['methods']:
                subset=[r for r in rows if int(r['requests'])==size and int(r['capacity'])==capacity
                        and r['mutant']==mutant and r['method']==method]
                per_fault.append({'requests':size,'capacity':capacity,'mutant':mutant,
                                  'split':'development' if mutant in plan['development_faults'] else 'evaluation',
                                  'method':method,'detected_at_16':sum(found(r,16) for r in subset),
                                  'trials':len(subset),'qualified':eligible(subset[0],plan)})
    save('per_mutant.csv',per_fault)
    # Pair by seed and resample that whole block across all configs and faults.
    differences=[]
    for budget in plan['budgets']:
        lookup={(r['requests'],r['capacity'],r['seed'],r['mutant'],r['method']):r
                for r in rows if eligible(r,plan)}
        blocks=[]
        for seed in range(plan['seeds']):
            values=[]
            for key,row in lookup.items():
                if row['method']!='model_conflicts' or int(row['seed'])!=seed: continue
                random_row=lookup[key[:-1]+('random',)]
                values.append(int(found(row,budget))-int(found(random_row,budget)))
            blocks.append(statistics.mean(values))
        rng=random.Random(20261106+budget)
        samples=[statistics.mean(rng.choices(blocks,k=len(blocks))) for _ in range(10000)]
        differences.append({'budget':budget,'model_minus_random_percentage_points':100*statistics.mean(blocks),
                            'cluster_bootstrap_95_low':100*percentile(samples,.025),
                            'cluster_bootstrap_95_high':100*percentile(samples,.975),
                            'resamples':10000,'seed_blocks':len(blocks)})
    save('paired_bootstrap.csv',differences)
    costs=read('costs.csv'); timing=[]
    for size,capacity in plan['configurations']:
        for method in plan['methods']:
            subset=[r for r in costs if int(r['requests'])==size and int(r['capacity'])==capacity
                    and r['method']==method]
            generation=[1000*float(r['generation_seconds']) for r in subset]
            replays=[1000*float(r['replay_seconds'])/(16*10) for r in subset]
            timing.append({'requests':size,'capacity':capacity,'method':method,
                           'median_suite_generation_ms':statistics.median(generation),
                           'median_runtime_replay_ms_including_audits':statistics.median(replays)})
    save('timing.csv',timing)
    text=['# Recorded study results','',
          'Four evaluation mutants pass the nominal schedule. One of them has an',
          'unreachable mutation branch at capacity one and is excluded for that configuration.',
          'Two other evaluation mutants fail nominal execution and are reported separately.','',
          '| Requests/capacity | Method | Budget 4 | Budget 16 |',
          '|---|---|---:|---:|']
    for size,capacity in plan['configurations']:
        for method in plan['methods']:
            relevant=[r for r in table if r['requests']==size and r['capacity']==capacity and r['method']==method]
            cells=[]
            for b in (4,16):
                row=next(r for r in relevant if r['budget']==b)
                cells.append(f"{row['detected']}/{row['eligible_trials']}")
            text.append(f"| {size}/{capacity} | {method} | {' | '.join(cells)} |")
    text+=['','## Paired model-minus-random detection differences','',
           '| Budget | Difference (percentage points) | 95% seed-cluster bootstrap interval |',
           '|---:|---:|---:|']
    for row in differences:
        text.append(f"| {row['budget']} | {row['model_minus_random_percentage_points']:.2f} | "
                    f"[{row['cluster_bootstrap_95_low']:.2f}, {row['cluster_bootstrap_95_high']:.2f}] |")
    (RESULTS/'summary.md').write_text('\n'.join(text)+'\n')
    print('\n'.join(text))

if __name__=='__main__': main()
