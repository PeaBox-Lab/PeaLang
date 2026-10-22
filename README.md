# PeaLang 0.26.0

PeaLang is an embeddable extension language for rules, workflows, automation, API orchestration, and controlled application customization.

## Install

```bash
python -m pip install pealang-0.26.0-py3-none-any.whl
pea --version
```

## Native asynchronous extension

```pea
async function load_employee(id) {
    return await hr.get(id)
}
export load_employee
```

```python
from pealang import AsyncVMRuntime, RuntimeOptions

runtime = AsyncVMRuntime(RuntimeOptions(
    permissions=frozenset({"hr.get"}),
    max_execution_ms=500,
))
runtime.register_async_function("hr.get", get_employee, "hr.get")
module = await runtime.load_async(source, "rules.pea")
employee = await module.call_async("load_employee", "E1001")
```

## Main capabilities

- Optional static types and semantic analysis
- PEAC bytecode compiler and VM
- Capability-safe synchronous and asynchronous embedding
- FastAPI integration
- VM debugging through DAP
- Structured exceptions, closures, defaults, and module imports

See `docs/ASYNC_VM.md`, `docs/FASTAPI_PACKAGE.md`, `docs/SEMANTIC_ANALYSIS.md`, and `docs/VM_CAPABILITIES.md`.
