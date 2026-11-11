# Changelog

## Repository layout

- Moved Python implementation and experiment entry points to `code/`.
- Updated reproduction commands, repository checks and GitHub Actions.

## 0.2.0 - 2026-11-07

- Checked the recorded numerical evidence against the supplied manuscript.
- Added an explicit paper-to-artifact map, fault identifiers and checking modes.
- Added a standard-library exporter for Tables 4-10 and Figure 4 curve data.
- Included exported CSV tables, including the first failing E1 execution prefix.
- Added paper-data export to the Python CI workflow.
- Rechecked the smoke entry point and deterministic statistical analysis.

The frozen scheduling algorithm, model interpreter, database implementation,
native Event-B proofs and original experimental measurements are unchanged.
Native Rodin was not rerun for this documentation and packaging release.
Remote GitHub Actions have not been executed during local preparation.

## 0.1.0 - 2026-11-06

- Packaged the recorded study with models, proofs, source code, raw results,
  reproduction commands, integrity checks and GitHub publishing instructions.
