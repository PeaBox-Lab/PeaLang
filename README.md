# PeaLang 0.22.0

PeaLang is an embeddable extension language for rules, workflows, automation, and controlled application customization.

## Install

```bash
python -m pip install pealang-0.22.0-py3-none-any.whl
pea --version
```

## Compile and run

```bash
pea compile app.pea
pea dis app.peac
pea vm app.peac
```

## Structured exceptions

```pea
try {
    throw "Something failed"
} catch error {
    print error
} finally {
    print "cleanup"
}
```

## Module imports

```pea
import "bonus.pea" as bonus
print bonus.calculate(100000)
```

## Default parameters

```pea
function calculate(amount, rate=0.10) {
    return amount * rate
}
```

## VM embedding

```python
from pealang import VMRuntime
runtime = VMRuntime(max_instructions=50_000)
module = runtime.load_file("rules.pea")
result = module.call("evaluate", {"employee_id": "E1001"})
```

## Documentation

See `docs/VM_EXCEPTIONS_MODULES.md`, `docs/BYTECODE_AND_VM.md`, `docs/VM_DEBUGGING.md`, `docs/VM_EMBEDDING.md`, and `docs/TYPE_SYSTEM.md`.
