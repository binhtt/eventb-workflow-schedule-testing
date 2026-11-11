# Reproducing the study

## Requirements and expected duration

The Python workflow uses Python 3.10+ and its standard-library sqlite3 module.
The recorded study used Python 3.12.14 and SQLite 3.53.1 on an x86_64 container.
The environment exposed nine logical CPUs on an Intel Xeon Platinum 8573C
and an 8 GiB memory limit. CPU affinity was not pinned.

The original main experiment took about 155 seconds. Finite conformance
and standalone timing add runtime. Allow several minutes for the full
Python reproduction, depending on the host. Timing values are machine
dependent.

## Entry points

From the repository root, run one of these commands.

```bash
python scripts/verify_artifact.py
python code/reproduce.py --mode smoke
python code/reproduce.py --mode analysis
python code/reproduce.py --mode full
```

The audit checks the source checksum list, the original scheduling/model
fingerprints, native proof metadata, core/proof model equivalence and
recorded count consistency. It reads the saved evidence.

The smoke run uses requests/capacity 2/1 and 4/2, with two seeds and the
same scheduling methods. It executes the unit checks, schedule bridge,
small complete-conformance instances and all nine mutants.

The analysis run copies the recorded data into its own workspace and
recomputes the qualified tables and paired bootstrap intervals.

The full run uses the paper's three configurations and 50 seeds. It runs
all unit checks, all three complete finite instances, all 96,000 main
replays, statistical analysis and the separate timing experiment.
Deterministic trial results and analysis tables are compared with the
recorded data automatically.

## Output isolation

Every run creates a fresh workspace under `outputs/`, or under a new path
supplied with `--output`. The source and recorded data remain unchanged.

A run directory contains `run.json`, `run.log` and `workspace/results/`.
The status JSON is updated to `passed` or `failed`. A failed workspace
and its log remain available for diagnosis. Existing destination
directories are rejected.

```bash
python code/reproduce.py --mode full --output outputs/reviewer-run
```

Changing the experimental plan for an exploratory run can be done in a
generated workspace. Such results belong to that changed plan and should
be reported separately from the recorded study.

## Native proof replay

Native reproving is described in [RODIN.md](RODIN.md).
The Python CI verifies saved proof artifacts and runs the executable
cross-checks. Rodin and Atelier B perform the native proof replay.

## Deterministic and machine-dependent outputs

The following should agree with the recorded study for an unchanged plan.

- First-detection records in `trials.csv`.
- Qualified detection counts and per-mutant tables.
- Seed-cluster bootstrap statistics, within numerical tolerance.
- Complete finite-state counts and the proof/source schedule digest.

Wall times, environment strings and derived timing summaries depend on
the machine and run conditions. The verifier compares deterministic
fields and leaves timing measurements available for inspection.

## CI

The workflow runs smoke validation on Python 3.10, 3.12 and 3.13.
A manual workflow-dispatch input enables the full Python reproduction.
The workflow definition is included with the prepared repository.
Its GitHub run status becomes available after the repository is pushed.
