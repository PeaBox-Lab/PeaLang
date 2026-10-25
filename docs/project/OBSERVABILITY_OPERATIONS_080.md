


# PeaLang 0.80 Observability and Operations Hardening

## Delivered
- W3C `traceparent` and `baggage` extraction/injection with context-local propagation.
- Dependency-free tracer and bounded exporter for OpenTelemetry adapters.
- Stable lower-snake-case `pealang_` metrics with series-cardinality protection.
- Separate liveness and readiness registries with critical checks and latency evidence.
- Bounded, redacted diagnostic ZIP bundles with per-entry SHA-256 manifests.

## Conventions
Use span names such as `vm.execute`, `connector.call`, `dag.node`, and `agent.tool`. Do not use user IDs, prompts, query text, or raw URLs as metric attributes. Liveness shows whether the process can operate; readiness covers dependencies required before accepting traffic. Diagnostic bundles deliberately omit source code and redact credential-like fields.

## Example
```python
from pealang.operations_hardening import Tracer, MetricRegistry, HealthRegistry
tracer = Tracer()
metrics = MetricRegistry(max_series=2000)
health = HealthRegistry()
health.add_liveness("runtime", lambda: True)
with tracer.span("connector.call", {"connector": "sql"}):
    metrics.record("connector_requests_total", 1, attributes={"connector": "sql", "outcome": "ok"})
```



