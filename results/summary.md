# Recorded study results

Four evaluation mutants pass the nominal schedule. One of them has an
unreachable mutation branch at capacity one and is excluded for that configuration.
Two other evaluation mutants fail nominal execution and are reported separately.

| Requests/capacity | Method | Budget 4 | Budget 16 |
|---|---|---:|---:|
| 2/1 | nominal | 0/150 | 0/150 |
| 2/1 | random | 94/150 | 146/150 |
| 2/1 | model_conflicts | 103/150 | 150/150 |
| 2/1 | canonical_independence | 25/150 | 25/150 |
| 4/2 | nominal | 0/200 | 0/200 |
| 4/2 | random | 189/200 | 200/200 |
| 4/2 | model_conflicts | 186/200 | 200/200 |
| 4/2 | canonical_independence | 88/200 | 88/200 |
| 8/3 | nominal | 0/200 | 0/200 |
| 8/3 | random | 197/200 | 200/200 |
| 8/3 | model_conflicts | 196/200 | 200/200 |
| 8/3 | canonical_independence | 156/200 | 156/200 |

## Paired model-minus-random detection differences

| Budget | Difference (percentage points) | 95% seed-cluster bootstrap interval |
|---:|---:|---:|
| 1 | 4.91 | [0.55, 9.27] |
| 2 | 2.55 | [-1.64, 6.73] |
| 4 | 0.91 | [-1.82, 3.64] |
| 8 | 0.00 | [-2.18, 2.18] |
| 16 | 0.73 | [0.18, 1.45] |
