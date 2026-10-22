# Capability-safe VM Embedding

```python
from pealang import VMRuntime, RuntimeOptions

runtime = VMRuntime(RuntimeOptions(
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

module = runtime.load_file("rules.pea")
result = module.call("evaluate", "E1001")
```

Without `employee.read`, the host call raises `PeaPermissionError`. Related functions can be registered with `register_module`. Inputs and outputs use the same portable conversion contract as `PeaRuntime`.

These are in-process controls. Execute hostile extensions in a dedicated process or container with operating-system limits.
