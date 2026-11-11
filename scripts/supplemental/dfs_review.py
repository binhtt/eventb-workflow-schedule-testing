from ablation_review import PLAN, ROOT, Model, MODEL_PATH, build_suite, eligible, fixture, json, replay

model = Model(MODEL_PATH)
coverage = json.loads((ROOT/'outputs/supplemental/coverage.json').read_text())
lookup = {(r['requests'],r['capacity'],r['seed']):r['common_prefix']
          for r in coverage if r['method']=='canonical_independence'}
results = {}
for size,capacity in PLAN['configurations']:
    operations,_ = fixture(size)
    hits = inside = 0
    for seed in range(PLAN['seeds']):
        suite,_ = build_suite('canonical_independence',size,capacity,seed,16,model)
        prefix = lookup[size,capacity,seed]
        for mutant in PLAN['evaluation_faults']:
            if not eligible({'mutant':mutant,'capacity':capacity},PLAN):
                continue
            _, first = replay(suite[0],size,capacity,mutant,model,operations)
            if first is not None:
                hits += 1
                inside += first <= prefix
    results[f'{size}/{capacity}'] = dict(first_schedule_audit_hits=hits, within_common_prefix=inside)
print(json.dumps(results,indent=2))
(ROOT/'outputs/supplemental/dfs_prefix.json').write_text(json.dumps(results,indent=2))
