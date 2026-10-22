# PeaLang 0.21.0

PeaLang is an embeddable extension language for rules, workflows, automation, and controlled application customization.

## Install

```bash
python -m pip install pealang-0.21.0-py3-none-any.whl
pea --version
```

## Compile and run

```bash
pea compile app.pea
pea dis app.peac
pea vm app.peac
```

## VM-backed extension

```python
from pealang import VMRuntime

runtime = VMRuntime(max_instructions=50_000)
module = runtime.load('''
function add(a, b) {
    return a + b
}
export add
''')

print(module.call("add", 10, 20))
```

## VM parity added in 0.21

- `break` and `continue`
- compound variable assignment
- property and index assignment
- `throw`
- breakpoints and continuation
- instruction stepping
- stack frames and locals
- compiled export invocation
- differential tests against the interpreter

## Type checking

```bash
pea typecheck rules.pea
```

## Documentation

See `docs/BYTECODE_AND_VM.md`, `docs/VM_DEBUGGING.md`, `docs/VM_EMBEDDING.md`, `docs/TYPE_SYSTEM.md`, and `docs/EMBEDDING.md`.
