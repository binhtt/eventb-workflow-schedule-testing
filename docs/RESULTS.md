# Recorded results and claim boundaries

## Formal and executable evidence

The shared-resource model has 24/24 native Rodin obligations discharged.
Complete finite-instance conformance checks cover 49,776 operation attempts
across 2,127 states. The main experiment contains 9,600 reference replays
and 86,400 mutant replays. All reference checks passed.

The three request/capacity settings are 2/1, 4/2 and 8/3. Each has 50 seeds,
four scheduling methods and a budget of 16 schedules. Budgets 1, 2, 4 and 8
are prefixes of those same suites.

## Qualification

The six reserved evaluation mutants are reported in the raw CSV files.
Two already fail nominal execution. Four pass nominal execution.
The wrong-request release mutation cannot activate at capacity one, where
a second lease cannot coexist with the current lease.

The qualified temporal denominator is 550 seed–mutant–configuration trials.
It represents four mutants across eleven eligible mutant/configuration
combinations, each with 50 seeds.

| Method | Budget 4 | Budget 16 |
|---|---:|---:|
| Nominal | 0/550 | 0/550 |
| Random | 480/550 | 546/550 |
| Model conflicts | 485/550 | 550/550 |
| Conservative sleep-set DFS | 269/550 | 269/550 |

The complete per-configuration breakdown is in
[results/qualified_summary.csv](../results/qualified_summary.csv).
The unqualified counts and split are preserved in
[results/per_mutant.csv](../results/per_mutant.csv) and
[results/trials.csv](../results/trials.csv).

## Statistical interpretation

At budget four, model conflicts exceeds random by 0.91 percentage points.
The exploratory paired seed-cluster bootstrap 95% interval is
[−1.82, 3.64]. At budget sixteen the difference is 0.73 percentage points,
with interval [0.18, 1.45]. All budget-specific intervals are retained.

The bootstrap uses 10,000 resamples of complete paired seed blocks.
The intervals are unadjusted for examining multiple budgets.
The result at budget four leaves the comparative advantage uncertain.

## Costs

Standalone timing randomizes method order in each of 30 repetitions per
configuration and uses seeds 1000–1029. Each measurement generates
16 schedules and replays the reference with conformance checks.

| Requests/capacity | Random median suite time | Model conflicts median suite time |
|---|---:|---:|
| 2/1 | 26.39 ms | 33.30 ms |
| 4/2 | 51.38 ms | 64.57 ms |
| 8/3 | 109.95 ms | 155.93 ms |

These measurements include generation, SQLite initialization and replay
audits. They exclude one-time model loading and native proof generation.
Timings reflect a shared container without CPU pinning.
The separate timing run adds 5,760 passing reference replays.

## Scope of supported conclusions

The artifact demonstrates a model-linked scheduling/conformance pipeline,
native model proofs and detection of selected implementation faults in a
constructed shared-resource workflow. It supplies detailed evidence for
the given model, implementation, hook granularity and mutation suite.

Broader efficiency claims require broader evidence. The observed
advantage over random is small, generation costs more, and the conservative
DFS baseline is traversal-sensitive. The study has one constructed case,
a handwritten adapter and same-study mutants.

[RESULTS_VI.md](RESULTS_VI.md) contains the detailed Vietnamese report.
