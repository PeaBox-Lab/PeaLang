# PeaLang v1.5.0 — Full-stack web server and auto-typed SDK generator

## Milestone: v1.5.0

### What was done
- Added `pealang/web_sdk.py` with enhanced web server features and TypeScript client generation
- `generate_typescript_client` — type-safe TypeScript client from route definitions
- `sse_endpoint_source` — Server-Sent Events endpoint boilerplate
- `websocket_handler_source` — WebSocket handler boilerplate
- `jwt_middleware_source` — JWT authentication middleware
- `rate_limiter_source` — rate limiter middleware
- `api_versioning_source` — API versioning middleware
- Registered in `analysis` and `stats`/`std.stats` namespaces
- Added `tests/test_web_sdk_v150.py` (7 tests) and `tests/test_use_cases_v150.py` (1 test)
- Added `docs/WEB_SDK.md` and `help/WEB_SDK.md`
- Added `examples/use_cases/39_web_sdk.pea`
- Version bumped to 1.5.0

### Test status
- 1047 tests passing

### Next steps (v1.6.0)
- Arrow/DuckDB vectorized DataFrame backend
- Pluggable execution backends (pure-Python + accelerated)
- Lazy query optimization (predicate pushdown, projection pushdown)