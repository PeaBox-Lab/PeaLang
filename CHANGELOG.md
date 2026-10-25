# Changelog

## 0.76.0 - 2026-10-25
- Added adversarial agent-policy probes and deterministic probe summaries.
- Added public API compatibility gating with explicit approved-removal handling.
- Added integrated test, security, API and file-retention release thresholds.
- Reorganized release notes, retention evidence and project metadata under `docs/` while retaining one root cumulative changelog and detailed README.

## 0.75.0 - 2026-10-25
- Added persistent SQLite agent audit trails, durable approval records, deterministic approval IDs, actor/reason capture, and audited tool-execution evidence.

## 0.73.0 - 2026-10-25
- Added optional ONNX Runtime inference, tensor/DataFrame and PyTorch interchange, and policy-governed natural-language query planning.

## 0.72.0 - 2026-10-25
- Merged interactive dashboard controls/bindings, browser REPL and dataset inspection, plus Jupyter kernel protocol and rich DataFrame rendering.

## 0.71.0 - 2026-10-24
- Combined three roadmap targets: dataset/column lineage, pipeline observability with SLA/alerts/audit, and a declarative dashboard DSL with React rendering.

## 0.70.0 - 2026-10-24
- Added durable SQLite orchestration state, retries with backoff/jitter, deterministic idempotency, interval scheduling, logical dates, run history, and backfill execution.

## 0.69.0 - 2026-10-24
- Added DAG/task definitions, dependency validation, cycle detection, deterministic topological ordering, execution layers, declarative graph loading, and local DAG execution.

## 0.68.0 - 2026-10-24
- Added RabbitMQ and WebSocket connectors, explicit RabbitMQ acknowledgement controls, QoS/prefetch, JSON messaging, and an in-memory message bus.

## 0.67.0 - 2026-10-24
- Added Kafka producer/consumer integration, consumer groups, manual commits, security options, batch publishing, and an in-memory test broker.

## 0.66.0 - 2026-10-24
- Added event-time streams, watermarks, late-event handling, tumbling/sliding windows, and persistent idempotent delivery semantics.

## 0.65.0 - 2026-10-24
- Added partitioning, bounded JSONL scans, predicate/projection pushdown, spill execution and checkpoints.


# Changelog
## 0.64.0a1 - 2026-10-24
- Added engine-neutral distributed compute plans and Local/Arrow/Polars/Spark adapters.
## 0.63.0rc2 - 2026-10-24
- RC2 stabilization: refreshed validation evidence, RC1 API compatibility checks and migration/operator guidance.
## 0.63.0rc1 - 2026-10-24
- Froze feature scope for RC1 and added API compatibility, deprecation policy, integration gates, threat model and migration guidance.
## 0.62.0 - 2026-10-24
- Added release-candidate packaging, SBOM/provenance, checksums, artifact verification, Containerfile, CI matrix and v1 readiness assessment.
## 0.61.0 - 2026-10-24
- Added secure Kubernetes YAML, security contexts, NetworkPolicy/PDB/topology controls, drain handling and RC stabilization checks.
## 0.60.0 - 2026-10-23
- Added distributed serving backends, load/performance gates, OpenTelemetry hooks and Kubernetes operations.
## 0.59.0 - 2026-10-23
- Added resilient serving with rate/concurrency limits, timeouts, logs/traces, secure loading, live reload and rollback.
## 0.57.0 - 2026-10-23
- Added portable pipelines, SQLite monitoring, policy/deployment manifests and MLOps CLI commands.
## 0.56.0 - 2026-10-23
- Added secure model bundles, monitoring stores, alerts, promotion gates, canary routing and rollback controls.
## 0.55.0 - 2026-10-23
- Added model bundles, inference/audit APIs, drift and fairness diagnostics, calibration, registry lifecycle and FastAPI serving.
## 0.54.0 - 2026-10-23
- Added production ML pipelines, cross-validation, tuning, regularization, multiclass classification and governance artifacts.
## 0.53.0 - 2026-10-23
- Added ML foundations: preprocessing, linear/logistic regression, evaluation, k-fold indices, persistence and pipelines.
## 0.52.0 - 2026-10-23
- Added forecasting baselines, evaluation metrics, seasonal decomposition, grouped forecasts, chart-ready series and optional acceleration benchmarks.
## 0.51.0 - 2026-10-23
- Added grouped and time-series analytics with resampling, shifts, changes, expanding/EWM windows and interpolation.
## 0.50.0 - 2026-10-23
- Added DataFrame analytics and statistics: summaries, quantiles, dispersion, correlation, frequencies, crosstabs, ranking, cumulative/rolling calculations, outliers and profiling.
## 0.49.0 - 2026-10-23
- Hardened connector runtime with token providers, profiles, health checks, certification matrices and Graph/SharePoint paging.
## 0.48.0 - 2026-10-23
- Added Microsoft Graph/SharePoint connector foundation, secret providers, capability metadata and connector certification.
## 0.47.0 - 2026-10-23
- Added S3, Azure Blob, ADLS Gen2 and GCS object storage connectors with common file and DataFrame operations.
## 0.46.0 - 2026-10-23
- Added OData and SFTP cloud connectors with pagination, query options, secure transfers and DataFrame ingestion.
## 0.45.0 - 2026-10-23
- Added Connector SDK with registry, transport abstraction, retries, auth helpers, REST and GraphQL connectors, pagination and DataFrame conversion.
## 0.44.0 - 2026-10-23
- Added SQL/database layer with SQLite, optional database adapters, discovery, parameterized queries, transactions, batching and SQLite upsert.
## 0.43.0 - 2026-10-23
- Added DataFrame Engine: joins, grouped aggregations, expressions, null handling, pivot/unpivot, window row numbers and expanded LazyFrame operations.
## 0.42.0 - 2026-10-23
- Added PeaLang Data foundation: schema model, DataFrame/LazyFrame, connector registry, CSV/JSON/JSONL and core transforms.
## 0.41.0 - 2026-10-23
- Added beta/pilot readiness model, candidate pilots, performance regression gate, security-review preparation and 1.0 migration-readiness report.
## 0.40.0 - 2026-10-23
- Added 500-case conformance corpus, differential runner, fuzz harness, security-boundary suite and multi-platform/Python CI definitions.
## 0.39.0 - 2026-10-23
- Added WebAssembly containers, browser ABI/policy, SDK and CLI.
## 0.38.0 - 2026-10-23
- Added native test/expect runner, filtering, coverage baseline, watch-mode portability baseline and migration CLI.
## 0.37.0 - 2026-10-23
- Added complete resource limit accounting and structured concurrency with cancellation propagation.
## 0.36.0 - 2026-10-23
- Added generic contracts/substitution/inference, protocols, project-wide contract analysis, and Result/Option/Future semantics foundation.
## 0.35.0 - 2026-10-23
- Stabilized the 14-module `std.*` standard library, capability gates, manifest, CLI inspection and compatibility tests.

## 0.35.0 - 2026-10-23
- Added implementation-independent language specification, EBNF grammar, feature stability registry, compatibility/deprecation contract, spec CLI, and revised foundational roadmap.

## 0.35.0 - 2026-10-23
- Added canonical registry indexes, sequence/replay protection, immutable version policy, package expiration, publisher namespaces, persistent registry state, and environment-based Bearer credentials.

## 0.35.0 - 2026-10-23
- Added Ed25519 public-key package signatures, public trust store, revocation, HTTPS registry transport, verified install, offline cache, and lockfile hash enforcement.

## 0.35.0 - 2026-10-23
- Added signed .peapkg support, trusted publisher keys, verification, safe extraction, HTTPS registry policy, installation receipts, and dependency-confusion defenses.

## 0.35.0 - 2026-10-23
- Added VM profiling, line coverage, benchmark tooling, and observer hooks.
- Added interpreter-versus-VM differential conformance coverage.
- Added source inventory/hash comparison and strengthened release integrity gates.
- Added profile/benchmark CLI commands and hardening documentation.

## 0.29.0 - 2026-10-22
- Added TypeScript SDK, React hooks, browser-safe capabilities, and schema UI integration.
## 0.28.0 - 2026-10-22
- Added Java runtime sidecar and Java SDK.
## 0.27.0 - 2026-10-22
- Added package ecosystem foundation.
## 0.26.0 - 2026-10-22
- Added native async VM.
## 0.24.0 - 0.25.0
- Added semantic analysis and FastAPI integration.
## 0.18.0 - 0.23.0
- Added embedding, types, compiler/VM, capability safety, exceptions, imports, and VM DAP.
## 0.1.0 - 0.17.0
- Established the language and tooling foundations.


## 0.74.0-alpha.1 - 2026-10-25
- Added agent dry-run tool planning.
- Added deterministic tool allow/deny policy gates.
- Added host approval gates for sensitive agent actions.
- Added tool-call budget enforcement.
- Moved historical development handovers to `docs/handover/` for a cleaner project root.
- Added agent governance documentation and regression tests.
