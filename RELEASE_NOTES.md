# PeaLang 0.25.0 Release Notes

PeaLang 0.25 adds the first production-oriented FastAPI integration layer.

## Added

- Optional `pealang[fastapi]` dependency group.
- `PeaExtensionRegistry` for semantic validation, startup loading, invocation, status, and development hot reload.
- `PeaRouter` for exposing PeaLang exports as FastAPI routes.
- OpenAPI metadata identifying the PeaLang extension and function behind each generated endpoint.
- Validation dependency factory.
- Controlled 400/403/429/500 error mapping.
- FastAPI exception handlers for permission and resource-limit failures.
- Extension status endpoint support.
- Complete FastAPI example application.
- Six dedicated FastAPI integration tests.
