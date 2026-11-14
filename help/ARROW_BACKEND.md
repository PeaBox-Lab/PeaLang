# Arrow/DuckDB vectorized DataFrame backend (v1.6.0)

PeaLang provides pluggable execution backends for DataFrame operations.

## Key functions

- `analysis.available_backends()` — list backends
- `analysis.preferred_backend()` — best backend
- `analysis.backend_info()` — backend info
- `analysis.create_query_plan(data)` — lazy query plan
- `.filter(pred)`, `.select(cols)`, `.limit(n)`, `.sort(key)`, `.collect()` — query operations