# Method and implementation boundaries

## Model-driven objectives

The core XML model is parsed into expression trees. Guards identify read
locations, and actions identify write locations. Singleton set membership
and singleton updates can be localized to one request. Scalar updates
remain shared locations.

A candidate objective pairs two operation instances when an action write
can affect the other's guard read. The generator uses protocol predecessors
to construct an ancestor prefix. It checks in the executable model that
both target operations are enabled, then schedules both validations before
their applications in a seeded orientation. A legal randomized suffix
completes the schedule. Remaining budget slots use random enabled-hook
scheduling.

Hook-to-event bindings and protocol predecessors come from the handwritten
adapter in `scheduling.py`. The parser supports the operators used in this
artifact and rejects unsupported expressions. It does not accept arbitrary
Event-B models.

## Service and oracle

The SQLite service stores pool availability, reservations, terminations,
handover state, effects and acknowledgements separately.
It imports neither the Event-B interpreter nor scheduling code.

Validation and application are separate scheduling hooks. Correct
applications revalidate their conditions. Each application is atomic at
the chosen scheduling granularity. The framework explores interleavings
between hooks.

The conformance checker compares acceptance and persistent state with
the corresponding abstract event or rejected-call stutter.
A separate audit of database state and observations checks conservation,
negative availability, closed requests holding reservations, effect
multiplicity and stale epochs.

The case uses scripted admission/worker responsibilities and explicit
environment expiry. It does not evaluate language-model behavior.

## Scheduling comparators

Nominal repeats one sequential schedule. Random samples uniformly among
currently enabled hooks, which induces a nonuniform distribution over
complete schedules.

The sleep-set DFS baseline only declares probe/probe pairs independent.
Application hooks remain dependent. This protects its independence
assumption against mutations that access an unexpected request key.
Its early-budget behavior depends strongly on DFS order, and its result
should not be interpreted as a comparison with every optimized DPOR tool.

A regression fixture checks all six raw schedules and the four retained
classes. Equivalent schedules have the same final state and property
verdict for the reference and all nine mutants.

## Mutation split and inference

The method and all mutants were constructed by the same study.
Three mutant implementations belong to development and six to reserved
evaluation. Related mechanisms occur across the split.

Qualification separates nominal failures and an unreachable mutation branch
at capacity one. Raw results preserve all configurations and mutants.
Intervals resample entire paired seed blocks across the configurations
and mutants. They are exploratory intervals across multiple budgets.
