# Robustness utilities (v136)

PeaLang provides dependency-free resilience and robustness utilities.

## Caching

- `LRUCache(capacity, ttl)` — LRU cache with optional TTL
- `memoize(func, capacity, ttl)` — memoize a function

## Retry

- `retry(func, max_attempts, delay, backoff)` — retry with exponential backoff
- `retry_call(func, *args, max_attempts, delay, backoff)` — retry a function call

## Circuit breaker

- `CircuitBreaker(failure_threshold, recovery_timeout)` — circuit breaker pattern
- `.call(func, *args)` — call through the breaker
- `.reset()` — reset the breaker
- `.status()` — get status

## Batch processing

- `batch_process(items, func, batch_size)` — process in batches
- `chunked(iterable, size)` — split into chunks
- `parallel_map(func, items, max_workers)` — parallel map (sequential fallback)

## Health monitoring

- `health_check(checks)` — run health checks
- `system_info()` — system information

## Data streaming

- `stream_records(records, chunk_size)` — yield chunks
- `lazy_filter(records, predicate)` — lazy filter
- `lazy_map(records, func)` — lazy map

## Fingerprinting

- `data_fingerprint(records)` — deterministic data hash
- `schema_fingerprint(schema)` — schema hash