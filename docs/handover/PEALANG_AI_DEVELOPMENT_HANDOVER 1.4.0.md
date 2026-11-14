# PeaLang v1.4.0 — Reactive React SDK and browser data grid

## Milestone: v1.4.0

### What was done
- Added `pealang/react_sdk.py` with React hook and adapter code generation
- `generate_react_hooks` — usePeaRuntime, usePeaScript, usePeaDataFrame, usePeaQuery, usePeaValidation
- `generate_data_grid_adapter` — zero-copy adapter for ag-Grid / TanStack Table
- `generate_chart_adapter` — adapter for Vega-Lite and Chart.js
- Registered in `analysis` and `stats`/`std.stats` namespaces
- Added `tests/test_react_sdk_v140.py` (5 tests) and `tests/test_use_cases_v140.py` (1 test)
- Added `docs/REACT_SDK.md` and `help/REACT_SDK.md`
- Added `examples/use_cases/38_react_sdk.pea`
- Version bumped to 1.4.0

### Test status
- 1040 tests passing

### Next steps (v1.5.0)
- Full-stack web server with SSE, WebSockets, JWT/OAuth2 middleware, rate limiting
- `pealang codegen ts` — TypeScript client generation from .pea route definitions