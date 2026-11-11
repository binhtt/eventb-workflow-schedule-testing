# Contributing

Open an issue describing the affected model, scheduling method, or recorded
result. Include Python/SQLite versions and a minimal schedule when reporting
a replay discrepancy.

Run the following before proposing changes.

```bash
python scripts/verify_artifact.py
python -m unittest discover -v -s code -p checks.py
python code/reproduce.py --mode smoke
```

The files in `results/` are the recorded study evidence. Generate new results
through `code/reproduce.py`, which writes to a separate workspace under `outputs/`.
Keep existing paper data unchanged when proposing an algorithm modification.

The original scheduling/model hashes remain in `frozen_generator.json`.
A changed algorithm or experimental plan belongs to a separately versioned
experiment with its own provenance and recorded results. Explain the scope
of any changed proof obligations, mutation qualification, or denominator.

The Python modules kept from the original study preserve their recorded
semantics. Native proof replay follows [docs/RODIN.md](docs/RODIN.md).

After reviewing an intended documentation edit, refresh the checksum inventory
with `python scripts/update_checksums.py` and run the audit again.
The original frozen-model fingerprints remain unchanged.
