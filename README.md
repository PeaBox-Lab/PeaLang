# PeaLang 0.27.0

PeaLang is an embeddable extension language for rules, workflows, automation, APIs, and controlled application customization.

## Install

```bash
python -m pip install pealang-0.27.0-py3-none-any.whl
pea --version
```

## Package workflow

```bash
pea pkg-init my-extension
cd my-extension
pea lock
pea install
pea audit
pea build
```

A package uses `pea.toml`, locks deterministic dependency metadata in `pea.lock`, installs local dependencies under `.pea_modules`, and builds a reproducible `.peapkg` archive.

## Mature runtime foundations

- Optional static types and semantic analysis
- PEAC bytecode compiler and VM
- Synchronous and native async embedding
- Capability-based host APIs
- FastAPI integration
- DAP debugging
- Structured exceptions, closures, imports, defaults
- Package manifests, locks, auditing, and reproducible builds

See `docs/PACKAGES.md`, `docs/ASYNC_VM.md`, `docs/FASTAPI_PACKAGE.md`, and `docs/SEMANTIC_ANALYSIS.md`.
