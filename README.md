# PeaLang 0.20.0

PeaLang is a readable, embeddable extension language for business rules, workflows, automation, integrations, and controlled application customization.

## Install

```bash
python -m pip install pealang-0.20.0-py3-none-any.whl
pea --version
```

## Compile and run bytecode

```bash
pea compile app.pea
pea dis app.peac
pea vm app.peac
pea app.peac
```

## Python compiler and VM API

```python
from pealang import compile_source_to_bytecode, VirtualMachine

module = compile_source_to_bytecode('print 2 + 3', 'demo.pea')
VirtualMachine().run(module)
```

## Existing embedding API

```python
from pealang import PeaRuntime, RuntimeOptions
runtime = PeaRuntime(RuntimeOptions(max_execution_ms=500))
module = runtime.load_file('rules.pea')
result = module.call('evaluate', {'employee_id': 'E1001'})
```

The embedding API remains interpreter-backed in 0.20. VM-backed modules will follow once parity and capability integration are complete.

## Type checking

```bash
pea typecheck rules.pea
```

## Documentation

See `docs/BYTECODE_AND_VM.md`, `docs/PEAC_FORMAT.md`, `docs/TYPE_SYSTEM.md`, and `docs/EMBEDDING.md`.
