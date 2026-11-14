"""Regression coverage for v136 robustness utilities."""

from pealang.robustness import (
    build_robustness_namespace,
    LRUCache,
    memoize,
    retry,
    retry_call,
    CircuitBreaker,
    batch_process,
    chunked,
    health_check,
    system_info,
    stream_records,
    lazy_filter,
    lazy_map,
    data_fingerprint,
    schema_fingerprint,
)


def test_lru_cache():
    cache = LRUCache(capacity=2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    cache.put("c", 3)
    assert cache.get("b") is None  # evicted
    stats = cache.stats()
    assert stats["size"] == 2
    assert stats["hits"] >= 1


def test_memoize():
    calls = {"n": 0}

    def f(x):
        calls["n"] += 1
        return x * 2

    mf = memoize(f)
    assert mf(5) == 10
    assert mf(5) == 10
    assert calls["n"] == 1


def test_retry():
    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ValueError("not yet")
        return "ok"

    result = retry(flaky, max_attempts=5, delay=0.01)
    assert result == "ok"
    assert attempts["n"] == 3


def test_circuit_breaker():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
    def fail():
        raise ValueError("boom")
    for _ in range(2):
        try:
            cb.call(fail)
        except ValueError:
            pass
    assert cb.state == "open"
    cb.reset()
    assert cb.state == "closed"


def test_batch_process():
    result = batch_process([1, 2, 3], lambda x: x * 2, batch_size=2)
    assert result == [2, 4, 6]


def test_chunked():
    chunks = chunked(range(7), 3)
    assert chunks == [[0, 1, 2], [3, 4, 5], [6]]


def test_health_check():
    result = health_check({"db": lambda: "ok", "cache": lambda: 42})
    assert result["status"] == "healthy"
    assert result["checks"]["db"]["status"] == "ok"


def test_system_info():
    info = system_info()
    assert "platform" in info
    assert "python" in info
    assert "cpu_count" in info


def test_stream_records():
    chunks = list(stream_records(range(5), chunk_size=2))
    assert chunks == [[0, 1], [2, 3], [4]]


def test_lazy_filter_map():
    assert lazy_filter([1, 2, 3, 4], lambda x: x > 2) == [3, 4]
    assert lazy_map([1, 2, 3], lambda x: x * 2) == [2, 4, 6]


def test_data_fingerprint():
    h1 = data_fingerprint([{"a": 1}, {"a": 2}])
    h2 = data_fingerprint([{"a": 1}, {"a": 2}])
    h3 = data_fingerprint([{"a": 1}, {"a": 3}])
    assert h1 == h2
    assert h1 != h3


def test_build_robustness_namespace():
    ns = build_robustness_namespace()
    assert "LRUCache" in ns
    assert "memoize" in ns
    assert "retry" in ns
    assert "CircuitBreaker" in ns
    assert "health_check" in ns
    assert len(ns) == 15
