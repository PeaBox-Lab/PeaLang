# Embedding PeaLang 0.18

PeaLang is intended to extend a host application without exposing arbitrary Python reflection or unrestricted operating-system access.

## Python host

```python
from pealang import PeaRuntime, RuntimeOptions

runtime = PeaRuntime(RuntimeOptions(
    permissions=frozenset({"employee.read"}),
    max_execution_ms=500,
    max_instructions=50_000,
    max_call_depth=100,
))

runtime.register_function(
    "employee.get",
    find_employee,
    permission="employee.read",
)

rules = runtime.load_file("rules.pea")
result = rules.call("evaluate", {"employee_id": "E1001"})
```

## PeaLang extension module

```pea
function evaluate(input) {
    let employee = employee.get(input.employee_id)
    return {"eligible": employee.active}
}
export evaluate
```

Only explicitly exported values can be obtained through `PeaModule`. Host functions are registered under controlled namespaces and may require capabilities.

## Value conversion

`to_pea` accepts null, booleans, numbers, strings, mappings, lists, tuples, sets, Python dataclasses, and Pydantic v2 models. `from_pea` can construct a dataclass or a Pydantic model from a PeaLang value.

## Resource boundaries

`RuntimeOptions` controls statement/instruction budget, elapsed execution time, call depth, permissions, and process availability. Process execution is disabled by default. These controls are safety boundaries for cooperative execution, not yet a hardened untrusted-code container. Execute hostile scripts in a separate operating-system process or container as an additional boundary.
