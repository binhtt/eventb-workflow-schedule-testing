# Native Event-B proof artifacts

## Recorded proof result

The `SharedWorkflow` project contains the `Pool` context and the
`Resource` machine. Rodin 3.9 checked both components accurately and
discharged all **24 generated obligations** automatically.

| Obligation kind | Count |
|---|---:|
| INV | 15 |
| THM | 6 |
| WD | 3 |

The successful run is recorded in
[proof/rodin_rest.log](../proof/rodin_rest.log).
[proof/summary.json](../proof/summary.json) records the prover profile.
Every saved status is automatic and discharged.

## Import

1. Install Rodin 3.9 and the Atelier B provers plugin.
2. Choose **File → Import → General → Existing Projects into Workspace**.
3. Select the archive
   `proof/SharedWorkflow_Rodin39_Proved.zip`.
4. Open `Resource` and inspect its proof obligations.

The inner archive contains model sources, static-check output,
obligations, proof trees and proof statuses.

## Reprove from source

Use a separate working directory for a clean native replay.

```bash
mkdir -p proof-run
cp proof/SharedWorkflow_Rodin39_Proved.zip proof-run/SharedWorkflow.zip
bash proof/rodin-atelier.sh --mode autoprove --strict --purge-proofs \
  --tactic-profile 'Workflow Atelier' /absolute/path/to/rodin \
  /absolute/path/to/proof-run SharedWorkflow.zip
```

The supplied Linux/macOS shell launcher uses Java 17 and the bundled Eclipse
compiler. Its `Workflow Atelier` profile combines default tactics,
built-in PP and Atelier B PP/ML, with ML forces 0–3 and a 10,000 ms timeout.
Rodin and the official Atelier B plugin must already be installed.
Windows users can import and reprove through the Rodin GUI.

## Proof parameters and tested semantics

Release and Expire introduce a parameter
`remaining = held ∖ {r}`. Derived guard theorems establish its partition,
disjointness and cardinality properties. These theorems are included
in the discharged obligations.

The normalization bridge substitutes the uniquely defined parameter
and removes the proved theorem guards. It checks exact equality of the
core guard/action expression trees and identical contexts.
The recorded verification also checks that all 600 suites, comprising
9,600 schedules, are identical for the two representations.

The model assumes finite REQ and positive integer CAP. Its invariants cover
resource conservation, free-capacity nonnegativity, exclusion of closed
requests from reservations, and acknowledgement history inclusion.
Execution exclusion is represented by its guard and monotone effected set.
The SQL audit additionally checks effect multiplicity and epochs at use time.

The proof result applies to the model. The independent implementation
evidence consists of the finite conformance checks and scheduled replays
documented in [RESULTS.md](RESULTS.md).
