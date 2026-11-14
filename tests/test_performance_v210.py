"""Regression coverage for v2.1.0 performance optimization."""

import tempfile
import os
from pathlib import Path

from pealang.performance import (
    build_performance_namespace,
    mmap_read,
    mmap_write,
    mmap_search,
    AdvancedCache,
    CachePolicy,
    ConnectionPool,
    Profiler,
    profile_function,
    optimize_batch_size,
    parallel_chunks,
    fast_hash,
)


def test_mmap_read_write():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.bin")
        data = b"hello world"
        mmap_write(path, data)
        result = mmap_read(path)
        assert result == data.decode("utf-8")


def test_mmap_search():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "test.bin")
        mmap_write(path, b"hello world hello")
        offsets = mmap_search(path, b"hello")
        assert len(offsets) == 2
        assert offsets[0] == 0


def test_advanced_cache_lru():
    cache = AdvancedCache(capacity=2, policy="lru")
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    cache.put("c", 3)
    assert cache.get("b") is None  # evicted
    stats = cache.stats()
    assert stats["size"] == 2


def test_advanced_cache_lfu():
    cache = AdvancedCache(capacity=2, policy="lfu")
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")  # access a
    cache.get("a")
    cache.put("c", 3)  # should evict b (least frequently used)
    assert cache.get("b") is None


def test_advanced_cache_ttl():
    cache = AdvancedCache(capacity=10, ttl=0.01)
    cache.put("a", 1)
    import time
    time.sleep(0.02)
    assert cache.get("a") is None  # expired


def test_connection_pool():
    pool = ConnectionPool(lambda: {"id": 1}, max_size=2)
    conn1 = pool.acquire()
    conn2 = pool.acquire()
    assert pool.stats()["in_use"] == 2
    pool.release(conn1)
    assert pool.stats()["in_use"] == 1
    pool.close_all()
    assert pool.stats()["total"] == 0


def test_profiler():
    prof = Profiler()
    with prof.time("test"):
        import time
        time.sleep(0.01)
    summary = prof.summary()
    assert "test" in summary
    assert summary["test"]["count"] == 1
    assert summary["test"]["mean_ms"] > 0


def test_profile_function():
    result = profile_function(lambda x: x * 2, 5)
    assert result["result"] == 10
    assert "elapsed_ms" in result


def test_optimize_batch_size():
    bs = optimize_batch_size(1000, item_cost_ms=1.0, overhead_ms=10.0)
    assert bs >= 1
    assert bs <= 1000


def test_parallel_chunks():
    chunks = parallel_chunks(range(10), num_chunks=3)
    assert len(chunks) >= 3
    assert sum(len(c) for c in chunks) == 10


def test_fast_hash():
    h1 = fast_hash({"a": 1, "b": 2})
    h2 = fast_hash({"b": 2, "a": 1})
    assert h1 == h2  # deterministic


def test_build_performance_namespace():
    ns = build_performance_namespace()
    assert "mmap_read" in ns
    assert "AdvancedCache" in ns
    assert "Profiler" in ns
    assert "fast_hash" in ns
    assert len(ns) == 11
