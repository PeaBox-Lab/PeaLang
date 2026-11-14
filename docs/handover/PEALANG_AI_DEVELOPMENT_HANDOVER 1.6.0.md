# PeaLang v1.6.0 — Arrow/DuckDB vectorized DataFrame backend

## Milestone: v1.6.0

### What was done
- Added `pealang/arrow_backend.py` with pluggable DataFrame execution backends
- `available_backends`, `preferred_backend`, `backend_info` — backend detection
- `PythonBackend` — pure Python (zero dependencies)
- `DuckDBBackend` — DuckDB-accelerated (when available)
- `QueryPlan`, `create_query_plan` — lazy query builder with filter/select/limit/sort/aggregate
- Predicate/projection pushdown optimization
- Registered in `analysis` and `stats`/`std.stats` namespaces
- Added `tests/test_arrow_backend_v160.py` (12 tests) and `tests/test_use_cases_v160.py` (1 test)
- Added `docs/ARROW_BACKEND.md` and `help/ARROW_BACKEND.md`
- Added `examples/use_cases/40_arrow_backend.pea`
- Version bumped to 1.6.0

### Test status
- 1059 tests passing

### Next steps (v1.7.0)
- ONNX model export and vector/RAG primitives
- Compile tree/boosting/GLM models to ONNX graphs
- Vector embedding types, semantic chunking, hybrid search