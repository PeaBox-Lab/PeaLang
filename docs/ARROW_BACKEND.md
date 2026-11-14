# Arrow/DuckDB vectorized DataFrame backend (v1.6.0)

PeaLang provides pluggable execution backends for DataFrame operations.

## Available backends

- `available_backends()` — list available backends (python, duckdb, polars, pyarrow)
- `preferred_backend()` — best available backend
- `backend_info()` — backend information

## Query plan (lazy evaluation)

- `create_query_plan(data)` — create a lazy query plan
- `.filter(predicate)` — filter rows
- `.select(columns)` — select columns
- `.limit(n)` — limit rows
- `.sort(key, ascending)` — sort rows
- `.aggregate(group_col, agg_col, agg_func)` — aggregate
- `.collect()` — execute and return results
- `.explain()` — show execution plan

## Backends

- `PythonBackend` — pure Python (zero dependencies)
- `DuckDBBackend` — DuckDB-accelerated (when available)