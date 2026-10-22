# PeaLang 0.35.0

PeaLang is an embeddable extension language for controlled rules, workflows, automation and host integration. Version 0.35 stabilizes its standard-library layer.

## Install
```bash
python -m pip install pealang-0.35.0-py3-none-any.whl
pea --version
```

## Run
```bash
pea run app.pea
pea repl
pea stdlib
pea spec
pea features
```

## Standard library
Use `std.collections`, `std.string`, `std.math`, `std.datetime`, `std.json`, `std.csv`, `std.regex`, `std.file`, `std.path`, `std.http`, `std.crypto`, `std.logging`, `std.testing`, and `std.concurrent`. Sensitive capabilities require explicit runtime permissions.

## Platform
PeaLang retains PEAC bytecode/VM, optional typing, semantic analysis, Python embedding, async VM, FastAPI integration, Java sidecar/client, TypeScript/React SDKs, DAP, package/signing/registry security and observability. See `docs/USER_GUIDE.md`, `docs/BASICS.md`, `FOUNDATIONAL_ROADMAP.md`, and `RELEASE_NOTES.md`.
