

# PeaLang v0.77 Performance and Memory Hardening

v0.77 starts the performance phase of the v1 hardening programme.

## Added
- Repeatable warm-up and timed performance probes.
- Mean and p95 latency reporting.
- Python allocation peak-memory measurement through `tracemalloc`.
- Explicit performance budgets with fail-closed PASS/FAIL evaluation.
- Dependency-free bounded LRU cache with eviction and hit-rate statistics.

Performance budgets are intentionally supplied by the caller because realistic limits differ between the VM, compiler, connectors, analytics and serving workloads.


