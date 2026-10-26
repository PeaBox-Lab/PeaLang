



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
- 0.81 compatibility and migration hardening: COMPLETED. Added deprecation lifecycle enforcement, deterministic/resumable/reversible migrations, public API snapshots and breaking-change gates. Focus: deprecation ledger, schema/config migrations, public API diff enforcement and upgrade fixtures.
- 0.82 packaging and reproducibility hardening: COMPLETED. Deterministic manifests, locked dependency evidence, CycloneDX SBOM verification, SLSA/in-toto provenance verification, Ed25519 signature verification and offline-install evidence are included.
- 0.83 runtime performance II: COMPLETED. Representative benchmark suites, percentile/throughput evidence, hot-path profiling, cache instrumentation, memory-pressure probes and prior-baseline regression gates are included.
- 0.84 concurrency and resilience: COMPLETED. Parent-child cancellation, deadline propagation, fail-fast structured task groups, retry/idempotency safety, graceful draining and resilience gates are included.
- 0.85 data/connector conformance: COMPLETED. Connector capability profiles, SQL dialect/binding/transaction contracts, streaming recovery semantics, object-store edge cases and certification gates are included.
- 0.86 ML/serving conformance: planned. Focus: model format compatibility, deterministic inference fixtures, serving overload/reload/rollback tests.
- 0.87 agent safety conformance: planned. Focus: tool isolation, approval durability, replay protection, budgets and auditable multi-step execution.
- 0.88 developer tooling stabilization: COMPLETED. LSP/DAP compatibility certification, diagnostic stability contracts, editor negotiation, reproducible debugging fixtures and tooling gates are included.
- 0.89 release-candidate hardening: COMPLETED. Feature families are frozen; blocker/high-severity defects, waivers and consolidated readiness evidence feed a single GO/NO-GO RC gate.
- 0.90 API freeze: COMPLETED. Frozen syntax/runtime/package/diagnostic/versioned-bytecode surfaces, canonical digests and approval-required breaking-change gates are active.
- 0.91 release candidate validation I: COMPLETED. Cross-platform/Python matrix contracts, upgrade validation, frozen-contract surveillance, soak aggregation and blocker/waiver gating are included.
- 0.92 release candidate validation II: COMPLETED. Evidence freshness, rollback/re-upgrade drills, drift/trend surveillance, ecosystem/recovery gates and waiver lifecycle controls are included.
- 0.93-0.96 release candidates: planned. Extended soak, recovery, reproducibility and ecosystem validation.
- 0.97-0.99 final documentation/ecosystem readiness: planned. Tutorials, examples, package/connector authoring guides and migration handbook.
- 1.0 stable: planned after all mandatory gates pass.




