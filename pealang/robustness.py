"""Robustness and resilience utilities for PeaLang.

Provides dependency-free caching, retry policies, batch processing,
health monitoring, and memory-efficient data operations for production
workloads.
"""

from __future__ import annotations

import json

import functools
import hashlib
import time
from collections import OrderedDict
from typing import Any, Callable, Iterable


# ---------------------------------------------------------------------------
# LRU Cache with TTL
# ---------------------------------------------------------------------------

class LRUCache:
    def __init__(self, capacity: int = 128, ttl: float | None = None):
        self.capacity = max(1, int(capacity))
        self.ttl = ttl
        self._cache: OrderedDict = OrderedDict()
        self._expiry: dict[Any, float] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: Any) -> Any:
        if key in self._cache:
            if self.ttl is not None and time.time() > self._expiry.get(key, 0):
                del self._cache[key]
                self._expiry.pop(key, None)
                self.misses += 1
                return None
            self._cache.move_to_end(key)
            self.hits += 1
            return self._cache[key]
        self.misses += 1
        return None

    def put(self, key: Any, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if self.ttl is not None:
            self._expiry[key] = time.time() + self.ttl
        if len(self._cache) > self.capacity:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
            self._expiry.pop(oldest, None)

    def clear(self) -> None:
        self._cache.clear()
        self._expiry.clear()

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {"size": len(self._cache), "capacity": self.capacity,
                "hits": self.hits, "misses": self.misses,
                "hit_rate": round(self.hits / total * 100, 2) if total else 0.0}


def memoize(func: Callable, capacity: int = 128, ttl: float | None = None) -> Callable:
    """Memoize a function with LRU cache."""
    cache = LRUCache(capacity=capacity, ttl=ttl)

    def wrapper(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        result = cache.get(key)
        if result is None and key not in cache._cache:
            result = func(*args, **kwargs)
            cache.put(key, result)
        return result

    wrapper.cache = cache
    wrapper.clear = cache.clear
    return wrapper


# ---------------------------------------------------------------------------
# Retry with exponential backoff
# ---------------------------------------------------------------------------

def retry(func: Callable, max_attempts: int = 3, delay: float = 1.0,
          backoff: float = 2.0, exceptions: tuple = (Exception,)) -> Any:
    """Retry a function with exponential backoff."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                time.sleep(delay * (backoff ** attempt))
    raise last_exc


def retry_call(func: Callable, *args, max_attempts: int = 3, delay: float = 1.0,
               backoff: float = 2.0, **kwargs) -> Any:
    """Retry a function call with arguments."""
    def wrapper():
        return func(*args, **kwargs)
    return retry(wrapper, max_attempts=max_attempts, delay=delay, backoff=backoff)


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half-open"
            else:
                raise RuntimeError("Circuit breaker is open")
        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as exc:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise exc

    def reset(self) -> None:
        self.state = "closed"
        self.failure_count = 0
        self.last_failure_time = 0.0

    def status(self) -> dict[str, Any]:
        return {"state": self.state, "failure_count": self.failure_count,
                "threshold": self.failure_threshold}


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def batch_process(items: Iterable, func: Callable, batch_size: int = 100) -> list[Any]:
    """Process items in batches, collecting results."""
    items = list(items)
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        for item in batch:
            results.append(func(item))
    return results


def chunked(iterable: Iterable, size: int) -> list[list[Any]]:
    """Split an iterable into chunks of given size."""
    items = list(iterable)
    return [items[i:i + size] for i in range(0, len(items), size)]


def parallel_map(func: Callable, items: Iterable, max_workers: int = 4) -> list[Any]:
    """Map a function over items (sequential fallback, no threading deps)."""
    return [func(item) for item in items]


# ---------------------------------------------------------------------------
# Health monitoring
# ---------------------------------------------------------------------------

def health_check(checks: dict[str, Callable] | None = None) -> dict[str, Any]:
    """Run health checks and return status."""
    checks = checks or {}
    results = {}
    overall = "healthy"
    for name, fn in checks.items():
        try:
            result = fn()
            results[name] = {"status": "ok", "result": result}
        except Exception as exc:
            results[name] = {"status": "error", "error": str(exc)}
            overall = "unhealthy"
    return {"status": overall, "checks": results, "timestamp": time.time()}


def system_info() -> dict[str, Any]:
    """Return basic system information."""
    import platform
    import os
    return {
        "platform": platform.system(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count() or 1,
        "cwd": os.getcwd(),
    }


# ---------------------------------------------------------------------------
# Data streaming / lazy evaluation
# ---------------------------------------------------------------------------

def stream_records(records: Iterable, chunk_size: int = 1000):
    """Yield chunks of records for memory-efficient processing."""
    chunk = []
    for r in records:
        chunk.append(r)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def lazy_filter(records: Iterable, predicate: Callable) -> list[Any]:
    """Filter records lazily, returning only matching items."""
    return [r for r in records if predicate(r)]


def lazy_map(records: Iterable, func: Callable) -> list[Any]:
    """Map a function over records lazily."""
    return [func(r) for r in records]


# ---------------------------------------------------------------------------
# Data hashing and fingerprinting
# ---------------------------------------------------------------------------

def data_fingerprint(records: Iterable) -> str:
    """Compute a deterministic fingerprint of a dataset."""
    rows = list(records or [])
    h = hashlib.sha256()
    for r in rows:
        h.update(json.dumps(r, sort_keys=True, default=str).encode())
    return h.hexdigest()


def schema_fingerprint(schema: Any) -> str:
    """Compute a fingerprint of a schema."""
    if hasattr(schema, "to_dict"):
        data = schema.to_dict()
    elif isinstance(schema, dict):
        data = schema
    else:
        data = str(schema)
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()



def build_robustness_namespace() -> dict[str, Any]:
    return {
        "LRUCache": LRUCache,
        "memoize": memoize,
        "retry": retry,
        "retry_call": retry_call,
        "CircuitBreaker": CircuitBreaker,
        "batch_process": batch_process,
        "chunked": chunked,
        "parallel_map": parallel_map,
        "health_check": health_check,
        "system_info": system_info,
        "stream_records": stream_records,
        "lazy_filter": lazy_filter,
        "lazy_map": lazy_map,
        "data_fingerprint": data_fingerprint,
        "schema_fingerprint": schema_fingerprint,
    }
