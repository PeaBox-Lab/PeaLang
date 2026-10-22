# PeaLang 0.25.0

PeaLang is an embeddable extension language for rules, workflows, automation, integrations, and controlled application customization.

## Install

Core runtime:

```bash
python -m pip install pealang-0.25.0-py3-none-any.whl
```

With FastAPI integration:

```bash
python -m pip install "pealang[fastapi]"
```

## FastAPI extension

```python
from fastapi import FastAPI
from pealang import RuntimeOptions, VMRuntime
from pealang.fastapi import PeaExtensionRegistry, PeaRouter

runtime = VMRuntime(RuntimeOptions(max_execution_ms=500, max_instructions=50000))
registry = PeaExtensionRegistry(runtime)
registry.load("hr", "rules.pea")
pea = PeaRouter(registry, prefix="/api").add("/bonus", "hr", "bonus").include_status()
app = FastAPI()
app.include_router(pea.router)
```

Run with:

```bash
uvicorn app:app --reload
```

## Documentation

See `docs/FASTAPI_PACKAGE.md`, `docs/SEMANTIC_ANALYSIS.md`, `docs/VM_CAPABILITIES.md`, and `docs/BYTECODE_AND_VM.md`.
