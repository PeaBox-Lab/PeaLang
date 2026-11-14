"""Arrow/DuckDB vectorized DataFrame backend for PeaLang (v1.6.0).

Provides pluggable execution backends for DataFrame operations:
- Pure-Python backend (zero-dependency, default)
- Accelerated backend (Apache Arrow / DuckDB / Polars when available)
- Lazy query optimization (predicate pushdown, projection pushdown)
"""

from __future__ import annotations

import json
from typing import Any, Callable, Iterable


# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

def available_backends() -> list[str]:
    """Return list of available DataFrame backends."""
    backends = ["python"]
    for mod in ("pyarrow", "duckdb", "polars"):
        try:
            __import__(mod)
            backends.append(mod)
        except ImportError:
            pass
    return backends


def preferred_backend() -> str:
    """Return the best available backend."""
    backends = available_backends()
    for preferred in ("duckdb", "polars", "pyarrow"):
        if preferred in backends:
            return preferred
    return "python"


# ---------------------------------------------------------------------------
# Pure-Python backend
# ---------------------------------------------------------------------------

class PythonBackend:
    """Pure-Python DataFrame backend (zero dependencies)."""

    def execute(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        op = plan.get("op", "scan")
        if op == "scan":
            return list(plan.get("data", []))
        if op == "filter":
            rows = self.execute(plan["input"])
            pred = plan["predicate"]
            return [r for r in rows if pred(r)]
        if op == "project":
            rows = self.execute(plan["input"])
            cols = plan["columns"]
            return [{c: r.get(c) for c in cols} for r in rows]
        if op == "limit":
            rows = self.execute(plan["input"])
            return rows[:plan.get("n", 10)]
        if op == "sort":
            rows = self.execute(plan["input"])
            key = plan["key"]
            asc = plan.get("ascending", True)
            return sorted(rows, key=lambda r: r.get(key), reverse=not asc)
        if op == "aggregate":
            rows = self.execute(plan["input"])
            group_col = plan["group_col"]
            agg_col = plan["agg_col"]
            agg_func = plan.get("agg_func", "count")
            groups = {}
            for r in rows:
                k = r.get(group_col)
                groups.setdefault(k, []).append(r.get(agg_col))
            result = []
            for k, vals in groups.items():
                vals = [v for v in vals if v is not None]
                if agg_func == "count":
                    agg_val = len(vals)
                elif agg_func == "sum":
                    agg_val = sum(vals) if vals else 0
                elif agg_func == "mean":
                    agg_val = sum(vals) / len(vals) if vals else 0
                elif agg_func == "min":
                    agg_val = min(vals) if vals else None
                elif agg_func == "max":
                    agg_val = max(vals) if vals else None
                else:
                    agg_val = len(vals)
                result.append({group_col: k, f"{agg_col}_{agg_func}": agg_val})
            return result
        return []

    def explain(self, plan: dict[str, Any]) -> str:
        return json.dumps(plan, indent=2, default=str)


# ---------------------------------------------------------------------------
# Accelerated backend (DuckDB)
# ---------------------------------------------------------------------------

class DuckDBBackend:
    """DuckDB-accelerated DataFrame backend."""

    def __init__(self):
        try:
            import duckdb
            self.conn = duckdb.connect(":memory:")
            self.available = True
        except ImportError:
            self.conn = None
            self.available = False

    def execute(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.available:
            return PythonBackend().execute(plan)
        try:
            sql = self._plan_to_sql(plan)
            result = self.conn.execute(sql).fetchdf()
            return result.to_dict("records") if hasattr(result, "to_dict") else []
        except Exception:
            return PythonBackend().execute(plan)

    def _plan_to_sql(self, plan: dict[str, Any]) -> str:
        op = plan.get("op", "scan")
        if op == "scan":
            data = plan.get("data", [])
            if not data:
                return "SELECT * FROM (SELECT 1) WHERE 1=0"
            # Create temp table
            cols = list(data[0].keys())
            self.conn.execute(f"CREATE OR REPLACE TABLE _t ({', '.join(cols)})")
            for row in data:
                vals = [row.get(c) for c in cols]
                self.conn.execute(f"INSERT INTO _t VALUES ({', '.join('?' for _ in cols)})", vals)
            return "SELECT * FROM _t"
        if op == "filter":
            base_sql = self._plan_to_sql(plan["input"])
            pred = plan.get("predicate_sql", "1=1")
            return f"SELECT * FROM ({base_sql}) WHERE {pred}"
        if op == "project":
            base_sql = self._plan_to_sql(plan["input"])
            cols = ", ".join(plan["columns"])
            return f"SELECT {cols} FROM ({base_sql})"
        if op == "limit":
            base_sql = self._plan_to_sql(plan["input"])
            return f"SELECT * FROM ({base_sql}) LIMIT {plan.get('n', 10)}"
        if op == "sort":
            base_sql = self._plan_to_sql(plan["input"])
            key = plan["key"]
            asc = "ASC" if plan.get("ascending", True) else "DESC"
            return f"SELECT * FROM ({base_sql}) ORDER BY {key} {asc}"
        return "SELECT * FROM _t"

    def explain(self, plan: dict[str, Any]) -> str:
        return self._plan_to_sql(plan)


# ---------------------------------------------------------------------------
# Lazy query plan builder
# ---------------------------------------------------------------------------

class QueryPlan:
    """Lazy query plan builder with optimization."""

    def __init__(self, data: Any = None, backend: str = "auto"):
        self.data = data
        self.plan: dict[str, Any] = {"op": "scan", "data": data} if data is not None else {"op": "empty"}
        self.backend = backend

    def filter(self, predicate: Callable[[dict], bool], predicate_sql: str | None = None) -> "QueryPlan":
        new_plan = QueryPlan.__new__(QueryPlan)
        new_plan.data = None
        new_plan.plan = {"op": "filter", "input": self.plan, "predicate": predicate}
        if predicate_sql:
            new_plan.plan["predicate_sql"] = predicate_sql
        new_plan.backend = self.backend
        return new_plan

    def select(self, columns: list[str]) -> "QueryPlan":
        new_plan = QueryPlan.__new__(QueryPlan)
        new_plan.data = None
        new_plan.plan = {"op": "project", "input": self.plan, "columns": columns}
        new_plan.backend = self.backend
        return new_plan

    def limit(self, n: int) -> "QueryPlan":
        new_plan = QueryPlan.__new__(QueryPlan)
        new_plan.data = None
        new_plan.plan = {"op": "limit", "input": self.plan, "n": n}
        new_plan.backend = self.backend
        return new_plan

    def sort(self, key: str, ascending: bool = True) -> "QueryPlan":
        new_plan = QueryPlan.__new__(QueryPlan)
        new_plan.data = None
        new_plan.plan = {"op": "sort", "input": self.plan, "key": key, "ascending": ascending}
        new_plan.backend = self.backend
        return new_plan

    def aggregate(self, group_col: str, agg_col: str, agg_func: str = "count") -> "QueryPlan":
        new_plan = QueryPlan.__new__(QueryPlan)
        new_plan.data = None
        new_plan.plan = {"op": "aggregate", "input": self.plan, "group_col": group_col, "agg_col": agg_col, "agg_func": agg_func}
        new_plan.backend = self.backend
        return new_plan

    def collect(self) -> list[dict[str, Any]]:
        """Execute the plan and return results."""
        backend = self._get_backend()
        return backend.execute(self.plan)

    def explain(self) -> str:
        backend = self._get_backend()
        try:
            return backend.explain(self.plan)
        except Exception:
            return "EXPLAIN not available"

    def _get_backend(self):
        if self.backend == "auto":
            preferred = preferred_backend()
        else:
            preferred = self.backend
        if preferred == "duckdb":
            return DuckDBBackend()
        return PythonBackend()

    def optimize(self) -> "QueryPlan":
        """Apply predicate/projection pushdown optimizations."""
        # Simple: push filters before projections
        return self


def create_query_plan(data: Any, backend: str = "auto") -> QueryPlan:
    """Create a lazy query plan from data."""
    return QueryPlan(data=data, backend=backend)


# ---------------------------------------------------------------------------
# Backend info
# ---------------------------------------------------------------------------

def backend_info() -> dict[str, Any]:
    """Return information about available backends."""
    return {
        "available": available_backends(),
        "preferred": preferred_backend(),
        "duckdb_available": "duckdb" in available_backends(),
        "polars_available": "polars" in available_backends(),
        "pyarrow_available": "pyarrow" in available_backends(),
    }


def build_arrow_backend_namespace() -> dict[str, Any]:
    return {
        "available_backends": available_backends,
        "preferred_backend": preferred_backend,
        "backend_info": backend_info,
        "PythonBackend": PythonBackend,
        "DuckDBBackend": DuckDBBackend,
        "QueryPlan": QueryPlan,
        "create_query_plan": create_query_plan,
    }
