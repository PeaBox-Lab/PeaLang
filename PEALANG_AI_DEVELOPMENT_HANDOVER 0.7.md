# PeaLang AI Development Handover v0.7.0

## Architecture
The v0.6 interpreter remains. `project.py` adds manifest discovery, project creation, dependency editing and module resolution. CLI project commands call this layer. `execute`/`Interpreter` accept optional project root and dependency metadata.

## Project contract
Manifest: `pea.json`; required `project.name`, `project.version`, `project.entry`; `dependencies` dictionary. Bare imports search project modules then dependency names then current-directory fallback. Explicit paths preserve earlier import behaviour.

## Dependency contract
Local paths only. A dependent PeaLang project resolves its configured entry file. No remote package installation, lockfile or version solving. Imports share globals.

## Documentation invariant
Every release includes detailed README, cumulative changelog, release notes, roadmap, additions/improvements, basics, foundations, user guide, help, reference/feature docs, test report, cumulative history and handover.

## Next
v0.7.1 should harden namespaces/dependency diagnostics/tooling before v0.8 agents/tools.
