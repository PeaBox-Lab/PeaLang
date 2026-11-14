"""Regression coverage for v1.6.0 Arrow/DuckDB backend."""

from pealang.arrow_backend import (
    build_arrow_backend_namespace,
    available_backends,
    preferred_backend,
    backend_info,
    PythonBackend,
    DuckDBBackend,
    QueryPlan,
    create_query_plan,
)


def test_available_backends():
    backends = available_backends()
    assert "python" in backends
    assert isinstance(backends, list)


def test_preferred_backend():
    pref = preferred_backend()
    assert pref in available_backends()


def test_backend_info():
    info = backend_info()
    assert "available" in info
    assert "preferred" in info
    assert "duckdb_available" in info


def test_python_backend_execute():
    backend = PythonBackend()
    plan = {"op": "scan", "data": [{"a": 1}, {"a": 2}]}
    result = backend.execute(plan)
    assert len(result) == 2
    assert result[0]["a"] == 1


def test_python_backend_filter():
    backend = PythonBackend()
    plan = {
        "op": "filter",
        "input": {"op": "scan", "data": [{"a": 1}, {"a": 5}, {"a": 3}]},
        "predicate": lambda r: r["a"] > 2,
    }
    result = backend.execute(plan)
    assert len(result) == 2


def test_python_backend_project():
    backend = PythonBackend()
    plan = {
        "op": "project",
        "input": {"op": "scan", "data": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]},
        "columns": ["a"],
    }
    result = backend.execute(plan)
    assert result == [{"a": 1}, {"a": 3}]


def test_python_backend_limit():
    backend = PythonBackend()
    plan = {
        "op": "limit",
        "input": {"op": "scan", "data": [{"a": i} for i in range(10)]},
        "n": 3,
    }
    result = backend.execute(plan)
    assert len(result) == 3


def test_python_backend_sort():
    backend = PythonBackend()
    plan = {
        "op": "sort",
        "input": {"op": "scan", "data": [{"a": 3}, {"a": 1}, {"a": 2}]},
        "key": "a",
        "ascending": True,
    }
    result = backend.execute(plan)
    assert result[0]["a"] == 1


def test_query_plan():
    data = [{"a": 1}, {"a": 5}, {"a": 3}]
    qp = create_query_plan(data)
    result = qp.filter(lambda r: r["a"] > 2).collect()
    assert len(result) == 2


def test_query_plan_chain():
    data = [{"a": 1, "b": 2}, {"a": 5, "b": 4}, {"a": 3, "b": 6}]
    qp = create_query_plan(data)
    result = qp.filter(lambda r: r["a"] > 2).select(["a"]).limit(1).collect()
    assert len(result) == 1
    assert "b" not in result[0]


def test_query_plan_explain():
    data = [{"a": 1}]
    qp = create_query_plan(data)
    plan_str = qp.explain()
    assert isinstance(plan_str, str)


def test_build_arrow_backend_namespace():
    ns = build_arrow_backend_namespace()
    assert "available_backends" in ns
    assert "create_query_plan" in ns
    assert "PythonBackend" in ns
    assert "DuckDBBackend" in ns
    assert len(ns) == 7
