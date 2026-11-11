"""Check the supplemental evidence and, optionally, a fresh reproduction."""
import argparse
import csv
import json
from pathlib import Path

from ablation_review import PLAN, ROOT, eligible

RECORDED = ROOT / 'results' / 'supplemental'
KEYS = ('requests', 'capacity', 'method', 'seed', 'mutant')
BUDGET = max(PLAN['budgets'])


def trial_key(row):
    return tuple(str(row[key]) for key in KEYS)


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def audit(directory):
    rows = json.loads((directory / 'ablation.json').read_text())
    baseline = {
        trial_key(row): int(row['first_detection']) if row['first_detection'] else None
        for row in read_csv(ROOT / 'results' / 'trials.csv')
    }
    audit = {trial_key(row): row['audit'] for row in rows}
    assert len(rows) == len(audit) == len(baseline) == 5400
    assert audit == baseline
    for row in rows:
        hits = [row[mode] for mode in ('conformance', 'audit') if row[mode] is not None]
        assert all(1 <= hit <= BUDGET for hit in hits)
        assert row['combined'] == min(hits, default=None)

    coverage = json.loads((directory / 'coverage.json').read_text())
    assert len(coverage) == 600
    for row in coverage:
        if row['method'] == 'model_conflicts':
            assert len(row['targeted_pairs']) == BUDGET
            assert row['distinct'] == BUDGET

    dfs = json.loads((directory / 'dfs_prefix.json').read_text())
    assert sum(row['first_schedule_audit_hits'] for row in dfs.values()) == 269
    assert sum(row['within_common_prefix'] for row in dfs.values()) == 267

    timings = read_csv(directory / 'timing.csv')
    expected_timing = {
        trial_key(row) for row in rows
        if row['method'] in ('random', 'model_conflicts') and eligible(row, PLAN)
    }
    assert len(timings) == len(expected_timing) == 1100
    assert {trial_key(row) for row in timings} == expected_timing
    for row in timings:
        assert (int(row['schedule']) if row['schedule'] else None) == audit[trial_key(row)]
        assert 0 <= float(row['generation_ms']) <= float(row['elapsed_ms'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--generated', type=Path)
    args = parser.parse_args()
    audit(RECORDED)
    if args.generated:
        audit(args.generated)
        for name in ('ablation.json', 'coverage.json', 'dfs_prefix.json'):
            assert json.loads((args.generated / name).read_text()) == json.loads(
                (RECORDED / name).read_text()
            ), name
    print('Supplemental evidence verified. Wall-clock measurements are environment-dependent.')


if __name__ == '__main__':
    main()
