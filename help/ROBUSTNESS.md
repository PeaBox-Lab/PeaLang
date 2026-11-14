# Robustness utilities (v136)

PeaLang provides dependency-free resilience and robustness utilities.

## Key functions

- `analysis.LRUCache(capacity, ttl)` — LRU cache
- `analysis.memoize(func, capacity, ttl)` — memoize
- `analysis.retry(func, max_attempts, delay, backoff)` — retry with backoff
- `analysis.CircuitBreaker(threshold, timeout)` — circuit breaker
- `analysis.batch_process(items, func, batch_size)` — batch processing
- `analysis.chunked(iterable, size)` — chunking
- `analysis.health_check(checks)` — health checks
- `analysis.system_info()` — system info
- `analysis.stream_records(records, chunk_size)` — streaming
- `analysis.lazy_filter(records, predicate)` — lazy filter
- `analysis.lazy_map(records, func)` — lazy map
- `analysis.data_fingerprint(records)` — data hash
- `analysis.schema_fingerprint(schema)` — schema hash