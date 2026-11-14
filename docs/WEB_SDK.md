# Full-stack web server and auto-typed SDK generator (v1.5.0)

PeaLang provides enhanced web server features and TypeScript client generation.

## TypeScript client generation

- `generate_typescript_client(routes, base_url, module_name)` — generate type-safe TypeScript client from route definitions

## Server features (source generators)

- `sse_endpoint_source()` — Server-Sent Events endpoint boilerplate
- `websocket_handler_source()` — WebSocket handler boilerplate
- `jwt_middleware_source()` — JWT authentication middleware
- `rate_limiter_source()` — rate limiter middleware
- `api_versioning_source()` — API versioning middleware