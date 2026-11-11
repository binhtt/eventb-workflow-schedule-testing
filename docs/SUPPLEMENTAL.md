# Supplemental experiments

The supplemental runs extend the shared-resource workflow artifact at base
commit `d1897ce2cfe4ebf4ac3937ad9fa926643d4e6405`. The Event-B model, workflow
implementation, mutants, scheduler and original experiment plan are identical
to those in the base commit.

## Reproduce the results

Use Python 3.10 or later. The Python scripts use only the standard library.
From the repository root, run the two commands sequentially so their timing
measurements do not contend with each other.

```sh
python code/reproduce.py --mode full
make supplemental
```

The first command creates a dated directory under `outputs/`. The second writes
to `outputs/supplemental/` and replaces earlier files at that path. The
deterministic results are checked against the recorded evidence. The wall-clock
measurements vary across runs. See [RODIN.md](RODIN.md) for the separate native
Rodin proof replay.

```sh
make test
make supplemental-audit
```

## Evidence and interpretation

| File in `results/supplemental/` | Evidence |
|---|---|
| `ablation.json` | First detecting replay for conformance only, property audits only, and their union, for all 5,400 mutant trials |
| `coverage.json` | Unique schedules, common hook prefix, sampled feasible objectives and targeted pairs |
| `dfs_prefix.json` | First-replay audit detections within the common prefix of the 16 DFS schedules |
| `timing.csv` | 1,100 audit-mode trials with generation and elapsed time, including runs censored after 16 replays |
| `summary.txt` | Detection, coverage and time-budget summaries |
| `rerun.json` | Environment and checks for this package |
| `native_rodin.log` | Clean native proof replay with the saved proofs purged |
| `primary_timing_rerun.csv` | New standalone reference-suite timing measurements for the original benchmark |
| `primary_timing_summary_rerun.csv` | Medians from the new reference-suite timing measurements |

The ablation projects two verdicts from each deterministic execution trace.
Its combined mode detects a trial as soon as either check flags a violation.
The audit-only first-detection indices match the original 5,400 trials.
Qualified results use 550 repeated seed–mutant–configuration trials per method.
The qualification applies to the original four eligible mutant implementations
and 11 eligible mutant–configuration combinations.

The coverage diagnostic attempts each precedence-filtered candidate once per
seed. A pair with a successful sampled prefix has a witnessed feasible prefix.
The procedure does not enumerate all prefix orders or count interactions
exercised incidentally by a selected schedule.

Elapsed-time detection uses property audits. It charges generation of the
complete 16-replay suite once per trial and charges whole replays through the
first detecting replay or the 16-replay cap. Detection times are descriptive.
The original reference-only timing data remain in their original paths, so the
numbers reported in the manuscript can be reproduced from those recorded files.

The study uses a constructed scripted workflow and seeded faults. Its scope is
controlled testing of shared-resource coordination at adapter hook boundaries.
