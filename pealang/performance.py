"""Performance optimization and advanced caching for PeaLang (v2.1.0).

Provides memory-mapped I/O, advanced caching with eviction policies,
connection pooling, and performance profiling for production workloads.
"""

from __future__ import annotations

import hashlib
import json
import mmap
import os
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Iterable


# ---------------------------------------------------------------------------
# Memory-mapped file I/O
# ---------------------------------------------------------------------------

def mmap_read(path: str, offset: int = 0, size: int | None = None) -> str:
    """Read a file using memory mapping for large files."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    file_size = p.stat().st_size
    read_size = size if size is not None else file_size - offset
    if read_size <= 0:
        return ""
    with open(path, "rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            return mm[offset:offset + read_size].decode("utf-8", "replace")


def mmap_write(path: str, data: Any, offset: int = 0) -> str:
    """Write data to a file using memory mapping."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    data = bytes(data)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    total_size = offset + len(data)
    if p.exists() and p.stat().st_size >= total_size:
        # Overwrite in place
        with open(path, "r+b") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE) as mm:
                mm[offset:offset + len(data)] = data
    else:
        # Write new file
        with open(path, "wb") as f:
            f.seek(total_size - 1)
            f.write(b"\x00")
        with open(path, "r+b") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE) as mm:
                mm[offset:offset + len(data)] = data
    return str(p)


def mmap_search(path: str, pattern: bytes) -> list[int]:
    """Search for a byte pattern in a memory-mapped file. Returns offsets."""
    offsets = []
    with open(path, "rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            start = 0
            while True:
                idx = mm.find(pattern, start)
                if idx == -1:
                    break
                offsets.append(idx)
                start = idx + 1
    return offsets


# ---------------------------------------------------------------------------
# Advanced caching with eviction policies
# ---------------------------------------------------------------------------

class CachePolicy:
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"


class AdvancedCache:
    """Advanced cache with multiple eviction policies."""

    def __init__(self, capacity: int = 128, policy: str = "lru", ttl: float | None = None):
        self.capacity = max(1, capacity)
        self.policy = policy
        self.ttl = ttl
        self._cache: dict[Any, Any] = {}
        self._access_count: dict[Any, int] = {}
        self._insertion_order: list[Any] = []
        self._expiry: dict[Any, float] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: Any) -> Any:
        if key not in self._cache:
            self.misses += 1
            return None
        if self.ttl is not None and time.time() > self._expiry.get(key, 0):
            self._evict(key)
            self.misses += 1
            return None
        self._access_count[key] = self._access_count.get(key, 0) + 1
        self.hits += 1
        return self._cache[key]

    def put(self, key: Any, value: Any) -> None:
        if key in self._cache:
            self._cache[key] = value
            self._access_count[key] = self._access_count.get(key, 0) + 1
            if self.ttl is not None:
                self._expiry[key] = time.time() + self.ttl
            return
        if len(self._cache) >= self.capacity:
            self._evict_one()
        self._cache[key] = value
        self._access_count[key] = 1
        self._insertion_order.append(key)
        if self.ttl is not None:
            self._expiry[key] = time.time() + self.ttl

    def _evict(self, key: Any) -> None:
        self._cache.pop(key, None)
        self._access_count.pop(key, None)
        self._expiry.pop(key, None)
        if key in self._insertion_order:
            self._insertion_order.remove(key)

    def _evict_one(self) -> None:
        if not self._cache:
            return
        if self.policy == "lru":
            # Least recently used = least access count
            key = min(self._access_count, key=lambda k: self._access_count.get(k, 0))
        elif self.policy == "lfu":
            key = min(self._access_count, key=lambda k: self._access_count.get(k, 0))
        elif self.policy == "fifo":
            key = self._insertion_order[0] if self._insertion_order else next(iter(self._cache))
        else:
            key = next(iter(self._cache))
        self._evict(key)

    def clear(self) -> None:
        self._cache.clear()
        self._access_count.clear()
        self._insertion_order.clear()
        self._expiry.clear()

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "size": len(self._cache),
            "capacity": self.capacity,
            "policy": self.policy,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total * 100, 2) if total else 0.0,
        }


# ---------------------------------------------------------------------------
# Connection pooling
# ---------------------------------------------------------------------------

class ConnectionPool:
    """Generic connection pool for database/HTTP connections."""

    def __init__(self, factory: Callable, max_size: int = 10, timeout: float = 30.0):
        self.factory = factory
        self.max_size = max_size
        self.timeout = timeout
        self._pool: list[Any] = []
        self._in_use: set[int] = set()
        self.created = 0

    def acquire(self) -> Any:
        # Try to reuse an existing connection
        for i, conn in enumerate(self._pool):
            if i not in self._in_use:
                self._in_use.add(i)
                return conn
        # Create new if under limit
        if len(self._pool) < self.max_size:
            conn = self.factory()
            self._pool.append(conn)
            idx = len(self._pool) - 1
            self._in_use.add(idx)
            self.created += 1
            return conn
        raise RuntimeError("Connection pool exhausted")

    def release(self, conn: Any) -> None:
        for i, c in enumerate(self._pool):
            if c is conn:
                self._in_use.discard(i)
                return

    def close_all(self) -> None:
        self._pool.clear()
        self._in_use.clear()

    def stats(self) -> dict[str, Any]:
        return {
            "total": len(self._pool),
            "in_use": len(self._in_use),
            "available": len(self._pool) - len(self._in_use),
            "max_size": self.max_size,
            "created": self.created,
        }


# ---------------------------------------------------------------------------
# Performance profiling
# ---------------------------------------------------------------------------

class Profiler:
    """Performance profiler with timing and memory tracking."""

    def __init__(self):
        self.timings: dict[str, list[float]] = {}
        self.counts: dict[str, int] = {}

    def time(self, name: str):
        """Context manager for timing a block."""
        import contextlib

        class _Timer:
            def __init__(self, profiler, name):
                self.profiler = profiler
                self.name = name
                self.start = 0

            def __enter__(self):
                self.start = time.perf_counter()
                return self

            def __exit__(self, *args):
                elapsed = time.perf_counter() - self.start
                self.profiler.timings.setdefault(self.name, []).append(elapsed)
                self.profiler.counts[self.name] = self.profiler.counts.get(self.name, 0) + 1

        return _Timer(self, name)

    def summary(self) -> dict[str, Any]:
        result = {}
        for name, times in self.timings.items():
            result[name] = {
                "count": self.counts.get(name, 0),
                "total_ms": round(sum(times) * 1000, 3),
                "mean_ms": round(sum(times) / len(times) * 1000, 3),
                "min_ms": round(min(times) * 1000, 3),
                "max_ms": round(max(times) * 1000, 3),
            }
        return result

    def reset(self) -> None:
        self.timings.clear()
        self.counts.clear()


def profile_function(func: Callable, *args, **kwargs) -> dict[str, Any]:
    """Profile a single function call."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return {"result": result, "elapsed_ms": round(elapsed * 1000, 3)}


# ---------------------------------------------------------------------------
# Batch optimizer
# ---------------------------------------------------------------------------

def optimize_batch_size(total_items: int, item_cost_ms: float = 1.0,
                        overhead_ms: float = 10.0) -> int:
    """Compute optimal batch size for processing."""
    if total_items <= 0:
        return 1
    # Simple heuristic: balance overhead vs per-item cost
    optimal = max(1, int((overhead_ms / item_cost_ms) ** 0.5))
    return min(optimal, total_items)


def parallel_chunks(items: Iterable, num_chunks: int = 4) -> list[list[Any]]:
    """Split items into N chunks for parallel processing."""
    items = list(items)
    if not items:
        return []
    chunk_size = max(1, len(items) // num_chunks)
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunks.append(items[i:i + chunk_size])
    return chunks


# ---------------------------------------------------------------------------
# Data fingerprinting (enhanced)
# ---------------------------------------------------------------------------

def fast_hash(data: Any) -> str:
    """Fast hash of any data structure."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def build_performance_namespace() -> dict[str, Any]:
    return {
        "mmap_read": mmap_read,
        "mmap_write": mmap_write,
        "mmap_search": mmap_search,
        "AdvancedCache": AdvancedCache,
        "CachePolicy": CachePolicy,
        "ConnectionPool": ConnectionPool,
        "Profiler": Profiler,
        "profile_function": profile_function,
        "optimize_batch_size": optimize_batch_size,
        "parallel_chunks": parallel_chunks,
        "fast_hash": fast_hash,
    }
