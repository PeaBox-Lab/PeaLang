# PeaLang 0.57.0

PeaLang is an embeddable extension language for controlled rules, workflows, automation and host integration. Version 0.37 completes runtime resource accounting and structured concurrency while retaining the v0.35 standard library and v0.36 type-system foundation.

## Install
```bash
python -m pip install pealang-0.57.0-py3-none-any.whl
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

## Connector SDK 0.45
Use the built-in REST and GraphQL connectors with runtime authentication headers, retry/backoff controls, pagination and direct DataFrame conversion. See `docs/CONNECTOR_SDK_045.md`.

## Cloud Connectors 0.46
OData and SFTP now extend the Connector SDK. See `docs/CLOUD_CONNECTORS_046.md`.

## Cloud Object Storage 0.47
Amazon S3, Azure Blob Storage, ADLS Gen2 and Google Cloud Storage now share a normalized object-storage API. See `docs/OBJECT_STORAGE_047.md`.

## Enterprise Connectors 0.48
Microsoft Graph/SharePoint, secret-provider abstractions, capability descriptors and certification checks extend the connector platform. See `docs/ENTERPRISE_CONNECTORS_048.md`.

## Connector Runtime 0.49
Production runtime profiles, renewable token providers, health diagnostics, certification matrices and Graph/SharePoint pagination.

## Data Analytics 0.50
PeaLang DataFrames now provide descriptive statistics, distributions, correlation, ranking, rolling/cumulative calculations, outlier detection and dataset profiles. See `docs/ANALYTICS_050.md`.

## Time-Series and Grouped Analytics 0.51
Date/time resampling, shifts, period changes, expanding/EWM windows, interpolation and grouped analytics now extend PeaLang DataFrames. See `docs/TIME_SERIES_051.md`.

## Forecasting and Accelerated Analytics 0.52
Baseline trend, moving-average and exponential-smoothing forecasts, evaluation, decomposition, grouped forecasting and chart-ready outputs extend the analytics stack. See `docs/FORECASTING_052.md`.

## Machine Learning Foundations 0.53
Dependency-light preprocessing, linear/logistic regression, evaluation, cross-validation indices and model persistence now extend PeaLang DataFrames. See `docs/ML_FOUNDATIONS_053.md`.

## Production ML 0.54
Fitted pipelines, cross-validation, tuning, regularization, multiclass classification, model cards and reproducibility manifests extend PeaLang ML. See `docs/PRODUCTION_ML_054.md`.

## ML Deployment and Monitoring 0.55
Model bundles, batch/audited inference, drift and fairness diagnostics, calibration, registry lifecycle and an optional FastAPI adapter extend production ML. See `docs/MLOPS_055.md`.

## Secure MLOps 0.56
Optional Ed25519 signing/Fernet encryption, monitoring event stores, alert operations, promotion policies, canary routing and rollback controls extend the ML platform. See `docs/SECURE_MLOPS_056.md`.

## Pipeline Portability and MLOps CLI 0.57
Versioned pipeline serialization, SQLite monitoring, alert policies, deployment manifests and `pea-ml` operations complete the next MLOps layer. See `docs/MLOPS_CLI_057.md`.

## Secure and Resilient Serving 0.59
Rate and concurrency controls, timeouts, structured logs, trace hooks, live reload, secure artifact loading and alert-driven rollback harden model serving. See `docs/RESILIENT_SERVING_059.md`.

## Distributed Serving and Kubernetes 0.60
Shared Redis-compatible state, distributed rate limiting, latency/load gates, OpenTelemetry hooks and Kubernetes resources extend resilient serving. See `docs/DISTRIBUTED_SERVING_060.md`.

## Kubernetes Security and RC Stabilization 0.61
Secure YAML manifests, non-root/read-only containers, NetworkPolicy, PDB, spread/anti-affinity, graceful draining, validation and soak tests harden distributed serving. See `docs/KUBERNETES_SECURITY_061.md`.

## Release Candidate Packaging 0.62
SBOM, provenance, checksums, artifact verification, non-root container packaging, CI matrix and v1 readiness gates establish the release-candidate supply chain. See `docs/SUPPLY_CHAIN_062.md`.

## Release Candidate 1 Stabilization
0.63 RC1 freezes feature scope and adds public API snapshots, compatibility/deprecation policy, integration gate reporting, threat modelling and upgrade guidance. See `docs/API_STABILITY_POLICY.md` and `RC1_GATE_STATUS.md`.
