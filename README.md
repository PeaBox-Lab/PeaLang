# PeaLang 0.44.0

PeaLang is an embeddable extension language for controlled rules, workflows, automation and host integration. Version 0.37 completes runtime resource accounting and structured concurrency while retaining the v0.35 standard library and v0.36 type-system foundation.

## Install
```bash
python -m pip install pealang-0.44.0-py3-none-any.whl
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

## Type system 0.36
Generics, structural protocol contracts, project-wide contract analysis and Result/Option/Future semantics are now part of the foundation. See `docs/TYPE_SYSTEM_036.md`.

## Runtime foundation 0.37
Resource budgets now cover time, instructions, memory, recursion, stack, collections, output, HTTP requests and file reads. Structured concurrency adds task groups and cancellation propagation.

## Native testing 0.38
Use `test "name" { expect condition }`, `pea test --filter`, `pea test --coverage`, and `pea migrate --from 0.37 --to 0.38 .`.

## WebAssembly 0.39
Use `pea wasm-build` and `pea wasm-inspect`. Executable lowering remains Preview.

## Conformance 0.40
Run `pea conformance` for the 500-case interpreter/VM gate and deterministic fuzz harness. GitHub Actions defines Windows/Linux/macOS and Python 3.10-3.13 matrices.

## Beta/pilot readiness 0.41
Run `pea readiness`. Candidate pilots and review packs are included, but the gate intentionally remains pending until two genuine pilots are validated.

## PeaLang Data 0.42
A new embeddable data foundation provides schemas, DataFrame/LazyFrame processing, a connector registry, CSV/JSON/JSONL IO and core transforms. See `DATA_ROADMAP.md`.


## PeaLang DataFrame Engine 0.43
Use joins, grouped aggregations, expression-based columns and filters, null handling, pivot/unpivot, row-number windows and lazy pipelines. See `docs/DATAFRAME_ENGINE_043.md`.

## SQL and Databases 0.44
SQLite works with the Python standard library. Adapter contracts also cover DuckDB, PostgreSQL, MySQL/MariaDB, SQL Server and Oracle through optional drivers. See `docs/SQL_DATABASES_044.md`.
