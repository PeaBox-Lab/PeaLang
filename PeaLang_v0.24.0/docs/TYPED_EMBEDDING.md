# Typed Embedding Contracts

Use PeaLang annotations as extension-contract documentation and run `pea typecheck` before loading a script. Python hosts should continue validating boundary values with dataclasses or Pydantic.

```python
from pealang import PeaRuntime, RuntimeOptions, TypeChecker

source = open("employee_rules.pea", encoding="utf-8").read()
result = TypeChecker().check(source, "employee_rules.pea")
if not result.ok:
    raise RuntimeError("Extension failed type validation")

runtime = PeaRuntime(RuntimeOptions(max_execution_ms=500))
module = runtime.load(source, "employee_rules.pea")
```

Typed PeaLang modules remain callable through `PeaModule.call`. Type annotations do not expose Python objects or bypass runtime permissions.
