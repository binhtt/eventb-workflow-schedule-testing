# Mapping the manuscript to the artifact

The table and figure numbers refer to the manuscript identified in
[MANUSCRIPT_MATCH.json](MANUSCRIPT_MATCH.json).

## Result locations

The ready-to-use CSV exports are in [results/paper_tables](../results/paper_tables).

| Manuscript evidence | Recorded source | CSV export |
|---|---|---|
| Table 4. Native Rodin proof obligations | `proof/SharedWorkflow/Resource.bps`, `.bpo`, `.bpr`, and `proof/summary.json` | `table4_proof_obligations.csv` |
| Table 5. Finite-instance conformance | `results/model_conformance.json` | `table5_finite_conformance.csv` |
| Table 6. Raw audit detections for nine mutants | `results/trials.csv` and `results/per_mutant.csv` | `table6_raw_mutant_detections.csv` |
| Table 7. Qualified audit detections by configuration | `results/trials.csv` and `results/qualified_summary.csv` | `table7_qualified_detection.csv` |
| Table 8. Paired oracle ablation | `results/supplemental/ablation.json` | `table8_oracle_ablation.csv` |
| Table 9. First failing prefix for E1 | `results/witnesses.json` | `table9_first_failing_prefix.csv` |
| Table 10. Interference coverage | `results/supplemental/coverage.json` | `table10_interference_coverage.csv` |
| Table 11. Paired seed-cluster bootstrap intervals | `results/paired_bootstrap.csv` | `table11_paired_bootstrap.csv` |
| Table 12. Median reference-suite timings | `results/supplemental/primary_timing_rerun.csv` and `primary_timing_summary_rerun.csv` in the same directory | `table12_suite_timing.csv` |
| Table 13. Cumulative audit detections by elapsed-time threshold | `results/supplemental/timing.csv` | `table13_elapsed_detection.csv` |
| Figure 4. Cumulative audit detections by replay budget | `results/trials.csv` | `figure4_detection_curve.csv` |

The Table 9 witness is `reserve_lost_update` under `model_conflicts`, with
requests/capacity (4, 2) and seed 0. The export ends at the first failing hook.
The model/proof bridge records 600 suites and 9,600 identical schedules in
`results/proof_bridge.json` and `results/proof_normalization.json`.
The main replay totals are recorded in `results/run_summary.json`. See
[RODIN.md](RODIN.md) for native proof replay and
[SUPPLEMENTAL.md](SUPPLEMENTAL.md) for the additional experiments.

Tables 12 and 13 use the archived measurements for the Intel Xeon Platinum
8370C environment described in the paper. Repeating the timing experiments on
another machine can produce different times and threshold counts.

## Fault identifiers

| Paper ID | Code identifier | Split |
|---|---|---|
| D1 | `reserve_cached` | Development |
| D2 | `execute_cached` | Development |
| D3 | `release_cached` | Development |
| E1 | `reserve_lost_update` | Reserved evaluation |
| E2 | `release_wrong_key` | Reserved evaluation |
| E3 | `execute_after_release` | Reserved evaluation |
| E4 | `execute_old_epoch` | Reserved evaluation |
| E5 | `transfer_credit` | Reserved evaluation |
| E6 | `ack_old_epoch` | Reserved evaluation |

## Checking modes and denominators

Reference schedules use acceptance/state conformance checks and property
audits. The main mutant-detection schedules use independent property audits
alone. Finite exploration also checks operation acceptance and successor state.

E5 and E6 fail nominal schedules, so they remain in the raw results but are
excluded from the qualified temporal analysis. E2 cannot activate its wrong-key
branch at capacity one. Four evaluation mutants across eleven eligible
mutant/configuration combinations and 50 seeds yield 550 trials per method.
These are not 550 distinct bugs. Budget-16 detection is 550/550 for model-derived
scheduling and 546/550 for random scheduling with audits alone. With the
combined checks, both schedulers reach 550/550. At budget four, audit counts are
485/550 and 480/550, and the paired interval includes zero.

## Export exact table data

```bash
python scripts/verify_artifact.py
python scripts/export_paper_results.py
```

Exports are written to a fresh `outputs/paper-tables/` directory. The command
refuses an existing output directory; use `--output outputs/another-export`
to retain earlier exports. It uses only the Python standard library and does
not modify the recorded experiment files.
