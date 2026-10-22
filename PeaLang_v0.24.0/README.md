# PeaLang 0.25.0

PeaLang is an embeddable extension language for rules, workflows, automation, integrations, and controlled application customization.

## Install

```bash
python -m pip install pealang-0.25.0-py3-none-any.whl
pea --version
```

## Semantic analysis

```bash
pea semantic src tests
```

Typed example:

```pea
type Employee = {
    name: String,
    rating: Int,
    salary: Number
}

function calculate_bonus(employee: Employee) -> Number {
    return employee.salary * 0.15
}
```

The analyzer checks typed returns, call arguments, record fields, unreachable code, nullability foundations, and expression compatibility.

## VM embedding

```python
from pealang import VMRuntime, RuntimeOptions
runtime = VMRuntime(RuntimeOptions(permissions=frozenset({"hr.get"})))
runtime.register_function("hr.get", find_employee, "hr.get")
module = runtime.load_file("rules.pea")
result = module.call("evaluate", "E1001")
```

## Documentation

See `docs/SEMANTIC_ANALYSIS.md`, `docs/TYPE_SYSTEM.md`, `docs/VM_CAPABILITIES.md`, `docs/VM_DAP.md`, and `docs/EMBEDDING.md`.
