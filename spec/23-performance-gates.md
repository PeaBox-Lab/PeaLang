# 4.0 Performance Gates

Wave 2 closes with a versioned performance gate that turns runtime evidence into
a CI-ready PASS/FAIL decision. It is additive to the frozen 3.0 core gate and
does not alter `CORE_SURFACES` or its manifest digest.

`GateBudget` records explicit limits for mean duration, p95 duration, peak
traced memory, and whether parity, conformance, and freeze checks are required.
`collect_gate_evidence()` runs a representative module through a
`PerformanceProbe`, verifies parallel-runtime and profiler parity, checks the v2
conformance suite, and checks the frozen 3.0 core gate. It returns `GateEvidence`
with timing values plus boolean release checks and a deterministic evidence
digest that excludes timing.

`performance_gate_report()` combines the format `pea-performance-gates-v4`,
schema version `4.0.0`, module and evidence digests, the budget, evidence,
derived checks, sorted issues, and a gate result. Timing evidence never directly
becomes a gate result; only the explicit budget comparisons and required boolean
checks do. `performance_gate()` recomputes the decision from a report so a stored
artifact cannot hide a changed budget or check.

The `pea perf-gate FILE.pea [--iterations N] [--workers N] [--emit FILE.json]`
command exposes the same behavior and writes the JSON report with `--emit`. The
`runtime.performance_gates_v4` feature flag records availability.
