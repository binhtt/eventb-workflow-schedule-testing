# Formal Verification and Schedule-Based Testing of Multi-Agent Workflows

Research artifact for the manuscript **Formal Verification and Schedule-Based
Testing of Multi-Agent Workflows**.

The artifact connects Event-B models, native Rodin proofs, scheduling
objectives extracted from guards/actions, and a separately implemented
SQLite workflow service. The case study covers bounded shared resources,
retry attempts, worker handover, acknowledgements, release and expiry.

## Quick start

Use Python **3.10 or later**, with the standard `sqlite3` module.
The Python experiments have no third-party dependencies.

From the repository root:

```bash
python scripts/verify_artifact.py
python code/reproduce.py --mode smoke
```

The smoke run exercises two small configurations with two seeds.
It writes a new directory under `outputs/`. The recorded results in
`results/` remain available for comparison.

To rerun the full Python study:

```bash
python code/reproduce.py --mode full
```

To recompute the analysis from the recorded raw trials:

```bash
python code/reproduce.py --mode analysis
```

To export the manuscript tables and cumulative detection-curve data:

```bash
python scripts/export_paper_results.py
```

See [docs/PAPER_RESULTS.md](docs/PAPER_RESULTS.md) for the mapping from paper
tables to raw data, fault identifiers, checking modes and qualification rules.
The corresponding ready-to-use CSV exports are in
[results/paper_tables](results/paper_tables).

Each command prints the generated results directory and the full log path.
Use `--output outputs/my-run` to choose a new directory. Existing output
directories are refused to protect previous runs.

## Recorded evidence

| Evidence | Recorded result |
|---|---:|
| Shared-resource model | 24/24 native Rodin obligations discharged automatically |
| Complete finite conformance checks | 49,776 operation attempts across 2,127 states |
| Reference replays in the main experiment | 9,600, all passing |
| Mutant replays in the main experiment | 86,400 |
| Scheduling configurations | Requests/capacity 2/1, 4/2 and 8/3 |
| Random seeds | 50 per configuration and method |
| Maximum budget | 16 schedules per suite |

The qualified temporal evaluation compares the following counts.

| Method | Detected by 4 schedules | Detected by 16 schedules |
|---|---:|---:|
| Nominal | 0/550 | 0/550 |
| Random enabled-hook scheduling | 480/550 | 546/550 |
| Model-derived guard-conflict scheduling | 485/550 | 550/550 |
| Conservative sleep-set DFS | 269/550 | 269/550 |

The denominator counts **seed–mutant–configuration trials**. It includes four
evaluation mutants, after excluding two nominal failures and one configuration
where the faulty branch cannot be activated. All raw trials remain in
[results/trials.csv](results/trials.csv).

The model-minus-random difference at budget four is 0.91 percentage points.
Its exploratory paired seed-cluster bootstrap 95% interval is
[−1.82, 3.64]. Model-derived generation also costs more in the recorded
timing study. These findings support the verified-model/testing pipeline
within this case study. They leave the comparative efficiency advantage
over random scheduling uncertain.

## Repository guide

| Path | Purpose |
|---|---|
| [model/SharedWorkflow](model/SharedWorkflow) | Core Event-B XML model and context |
| [proof/SharedWorkflow](proof/SharedWorkflow) | Proved native project, including proof trees and statuses |
| [proof/SharedWorkflow_Rodin39_Proved.zip](proof/SharedWorkflow_Rodin39_Proved.zip) | Archive for direct import into Rodin |
| [code/](code/) | Python implementation, checks, and experiment entry points |
| [code/eventb.py](code/eventb.py) | Strict interpreter for the supported Event-B subset |
| [code/scheduling.py](code/scheduling.py) | Objective extraction, schedule generation and baselines |
| [code/runtime.py](code/runtime.py) | Independent SQLite implementation and nine mutants |
| [code/experiment.py](code/experiment.py) | Paired fixed-budget experiment |
| [code/validate_model.py](code/validate_model.py) | Complete finite-instance conformance checks |
| [code/proof_bridge.py](code/proof_bridge.py) | Normalize proof-only parameters and theorem guards |
| [results](results) | Recorded raw data, witnesses, summaries and environment |
| [docs](docs) | Method, result interpretation, data dictionary and reproduction guide |
| [scripts/export_paper_results.py](scripts/export_paper_results.py) | Export paper table data and the full first-detection curve without changing raw results |
| [.github/workflows/reproducibility.yml](.github/workflows/reproducibility.yml) | Python smoke CI and optional full reproduction |

## Supplemental experiments

The release also includes paired oracle ablation, interference-objective
coverage, sleep-set DFS prefix analysis, and elapsed-time detection.
Run `make supplemental` and see [docs/SUPPLEMENTAL.md](docs/SUPPLEMENTAL.md)
for the data dictionary and interpretation. The recorded data are under
[results/supplemental](results/supplemental).

## Native Rodin verification

The recorded native run used **Rodin 3.9** and the **Atelier B provers**.
There are 15 invariant, six theorem and three well-definedness obligations.
Proof-only parameters for release/expiry are explicitly defined and normalized
back to the tested event semantics.

The Python artifact audit checks saved proof metadata and operational
equivalence. Native proof replay uses Rodin and its prover plugins.
Follow [docs/RODIN.md](docs/RODIN.md) for import and clean reproving.

## Scope

The artifact evaluates one constructed workflow with controlled scheduling
hooks and scripted roles. Hook bindings and protocol order are supplied by
a handwritten adapter. The model parser supports the expression subset used
by this artifact. The SQL implementation is separately coded from the model.

All mutation operators and the method were developed in the same study.
The reserved evaluation split separates mutant implementations, with related
mechanisms across the split. Applications are atomic at the apply hook.
Expiry is a permitted environment operation after reservation. Claims concern
the modeled protocol and finite implementation checks.

See [docs/RESULTS.md](docs/RESULTS.md) for qualification, statistical limits
and the interpretation of the conservative reduction baseline.

## Citation and license

Use [CITATION.cff](CITATION.cff) when citing the software.
The artifact is licensed under [MIT](LICENSE).
The adapted headless launcher retains its upstream
[license and attribution](THIRD_PARTY_NOTICES.md).

## Publish this prepared repository

After installing GitHub CLI and signing into your account:

```bash
gh auth login
bash scripts/publish_github.sh --private
```

Choose `--public` when you intend to publish the artifact publicly.
The script resolves the authenticated owner, checks the artifact, creates
the repository and pushes the reviewed files. It refuses an existing
repository name. Its default name is `eventb-workflow-testing`.

GitHub CLI behavior is described in the
[official repository-creation manual](https://cli.github.com/manual/gh_repo_create).
