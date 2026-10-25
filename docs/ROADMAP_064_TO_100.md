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
- 0.77 ONNX Runtime bridge.
- 0.78 PyTorch and tensor/DataFrame interchange.
- 0.79 governed natural-language query planning.
- 0.80 agent dry-run, validation, policy and approval gates.

## Phase E: v1 stabilization
- 0.81-0.89 performance, security and enterprise integration hardening.
- 0.90 API freeze.
- 0.91-0.99 release candidates and live certification.
- 1.0 only after automated and external gates pass.

