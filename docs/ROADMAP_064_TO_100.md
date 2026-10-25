# PeaLang Roadmap: 0.64 to 1.0

The 0.63 RC line remains frozen. New capabilities resume in the 0.64 alpha line.

## Priority based on current user fit
PeaLang currently fits enterprise data engineering and embedded analytics best: HR systems and automation teams, Python/Java/FastAPI integrators, and local-first enterprise developers. Prioritize scalable execution and orchestration before dashboards, notebooks, deep learning, and autonomous analytics.

## Phase A: Scalable data
- 0.64 engine-neutral Local/Arrow/Polars/Spark execution plans.
- 0.65 partitions, spilling, pushdown, checkpoints and out-of-memory scans.
- 0.66 event-time streaming, windows, watermarks and delivery semantics.
- 0.67 Kafka connector.
- 0.68 RabbitMQ and WebSocket connectors.

## Phase B: Orchestration and governance
- 0.69 DAG definitions and dependency validation.
- 0.70 state, retries, backfill, idempotency and scheduling. COMPLETED
- 0.71 dataset and column lineage. COMPLETED (merged release)
- 0.72 pipeline observability, SLAs and audit reports.

## Phase C: Interactive analytics
- 0.73 declarative dashboard syntax and React renderer.
- 0.74 interactive controls, tables and chart bindings. COMPLETED IN 0.72
- 0.75 browser REPL and dataset inspector. COMPLETED IN 0.72
- 0.76 Jupyter kernel and inline rendering. COMPLETED IN 0.72

## Phase D: Advanced ML and governed agents
- 0.77 ONNX Runtime bridge. COMPLETED IN 0.73
- 0.78 PyTorch and tensor/DataFrame interchange. COMPLETED IN 0.73
- 0.79 governed natural-language query planning. COMPLETED IN 0.73
- 0.80 agent dry-run, validation, policy and approval gates.

## Phase E: v1 stabilization
- 0.81-0.89 performance, security and enterprise integration hardening.
- 0.90 API freeze.
- 0.91-0.99 release candidates and live certification.
- 1.0 only after automated and external gates pass.

## Current execution update after 0.78
The roadmap version numbers for advanced ML were delivered early in 0.73, and interactive work was consolidated in 0.72. The active release line is now using 0.77+ for v1 stabilization.

- 0.77 performance and memory hardening: COMPLETED.
- 0.78 trust-boundary security hardening: COMPLETED in this build.
- 0.79 enterprise integration hardening: COMPLETED. Focus: identity/credential-provider interfaces, connector reliability contracts, TLS/proxy configuration normalization, structured retry/circuit-breaker policy.
- 0.80 observability and operations hardening: COMPLETED. W3C/OpenTelemetry-compatible context propagation, metric conventions/cardinality limits, health/readiness contracts and bounded redacted diagnostic bundles.
- 0.81 compatibility and migration hardening: planned. Focus: deprecation ledger, schema/config migrations, public API diff enforcement and upgrade fixtures.
- 0.82 packaging and reproducibility hardening: planned. Focus: deterministic builds, locked dependency evidence, SBOM/provenance verification and offline install validation.
- 0.83 runtime performance II: planned. Focus: representative benchmark suites, optimizer hot paths, cache instrumentation and memory-pressure behavior.
- 0.84 concurrency and resilience: planned. Focus: cancellation/timeout propagation, structured concurrency stress tests, retry safety and graceful shutdown.
- 0.85 data/connector conformance: planned. Focus: SQL dialect matrices, streaming failure semantics, object-store edge cases and connector certification.
- 0.86 ML/serving conformance: planned. Focus: model format compatibility, deterministic inference fixtures, serving overload/reload/rollback tests.
- 0.87 agent safety conformance: planned. Focus: tool isolation, approval durability, replay protection, budgets and auditable multi-step execution.
- 0.88 developer tooling stabilization: planned. Focus: LSP/DAP/editor compatibility, diagnostics stability and reproducible debugging.
- 0.89 release-candidate hardening: planned. No new feature families; close blocker/high-severity defects and complete release evidence.
- 0.90 API freeze: planned. Freeze public syntax/runtime/package APIs for 1.0, with only approved compatibility fixes afterward.
- 0.91-0.96 release candidates: planned. Cross-platform soak, upgrade, security, performance and ecosystem validation.
- 0.97-0.99 final documentation/ecosystem readiness: planned. Tutorials, examples, package/connector authoring guides and migration handbook.
- 1.0 stable: planned after all mandatory gates pass.
