# PeaLang 0.18.0

PeaLang is a readable, embeddable extension language for business rules, workflows, automation, integrations, and controlled application customization.

## Install

```bash
python -m pip install pealang-0.18.0-py3-none-any.whl
pea --version
```

## Embed in Python

```python
from pealang import PeaRuntime, RuntimeOptions

runtime = PeaRuntime(RuntimeOptions(
    permissions=frozenset({"employee.read"}),
    max_execution_ms=500,
    max_instructions=50_000,
))
runtime.register_function("employee.get", find_employee, "employee.read")
module = runtime.load_file("rules.pea")
result = module.call("evaluate", {"employee_id": "E1001"})
```

## Extension script

```pea
function evaluate(input) {
    let employee = employee.get(input.employee_id)
    return {"eligible": employee.active}
}
export evaluate
```

## CLI

```bash
pea run examples/hello.pea
pea repl
pea check examples
pea fmt examples
pea test
pea dap
```

## Security defaults

Embedded process execution is disabled. Host functions must be explicitly registered and can require permissions. Set time, instruction, and call-depth budgets. Use a separate process or container for hostile code because 0.18 is a cooperative in-process sandbox, not yet a hardened security boundary.

## Integration examples

- `examples/embedding/python_host.py`
- `examples/embedding/fastapi_app.py`
- `docs/EMBEDDING.md`
- `docs/FASTAPI_INTEGRATION.md`
- `docs/JAVA_REACT_INTEROP.md`
