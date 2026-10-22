# PeaLang FastAPI Integration

Install optional dependencies:

```bash
python -m pip install "pealang[fastapi]"
```

Core components:

- `PeaExtensionRegistry`: semantic validation, loading, status, hot reload, invocation.
- `PeaRouter`: expose exported PeaLang functions as HTTP routes.
- `create_validation_dependency`: invoke a PeaLang validator before application logic.
- `install_exception_handlers`: map permission and resource-limit errors to controlled HTTP responses.

## Example

```python
from fastapi import FastAPI
from pealang import RuntimeOptions, VMRuntime
from pealang.fastapi import PeaExtensionRegistry, PeaRouter

runtime = VMRuntime(RuntimeOptions(max_execution_ms=500, max_instructions=50000))
registry = PeaExtensionRegistry(runtime, hot_reload=False)
registry.load("hr", "rules.pea")
router = PeaRouter(registry, prefix="/api")
router.add("/bonus", "hr", "bonus")
router.include_status()
app = FastAPI()
app.include_router(router.router)
```

Generated OpenAPI operations contain `x-pealang-extension` and `x-pealang-function` metadata.
