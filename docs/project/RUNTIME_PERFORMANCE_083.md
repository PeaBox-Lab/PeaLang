
# PeaLang 0.83 Runtime Performance II

## Delivered
- Named representative benchmark suites with warmup and repeatable iterations.
- Mean, p50, p95, p99, throughput/sec and peak-memory evidence.
- Versioned benchmark baselines and automatic comparison with the previous release.
- Configurable regression budgets for latency, throughput and memory.
- Named hot-path profiler for compiler, optimizer and runtime sections.
- LRU cache instrumentation for hits, misses, loads and evictions.
- Repeated memory-pressure probes measuring peak and retained growth.

## Default regression budgets
- Mean latency: no more than 10% regression.
- p95 latency: no more than 15% regression.
- p99 latency: no more than 20% regression.
- Peak memory: no more than 15% regression.
- Throughput: at least 90% of the baseline.

These defaults are release gates, not absolute performance claims. Baselines should be generated on stable, comparable hardware and runtime configurations.

