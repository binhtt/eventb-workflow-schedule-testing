# Third-party notices

The headless Rodin launcher and its shell helpers derive from
[eventb-rossi/rodin-headless](https://github.com/eventb-rossi/rodin-headless),
commit `c5e91ab55f9862bd3bd064d235db0bb612577616`.

The upstream license is MIT, copyright 2025 Denis Efremov.
The complete notice is preserved in [proof/LAUNCHER_LICENSE](proof/LAUNCHER_LICENSE).

The local adaptation uses the bundled Eclipse compiler on Java 17,
omits ProB integration, and registers the Workflow Atelier tactic profile.
It preserves the Rodin proof generator and official prover binaries.

Rodin, Eclipse and Atelier B binaries are obtained separately under their
respective licenses. This repository contains generated proof artifacts
and model sources, together with the launcher scripts.
