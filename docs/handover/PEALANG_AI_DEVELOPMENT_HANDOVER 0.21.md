



# PeaLang AI Development Handover 0.21

## Delivered

Version 0.21 extends the PEAC compiler and VM with loop-control patching, assignment parity, throw, debugger state, and VM-backed extension invocation.

Primary files:

- `pealang/bytecode.py`
- `pealang/compiler.py`
- `pealang/vm.py`
- `pealang/vm_embedding.py`
- `tests/test_vm_parity_v021.py`

## Important limits

- `throw` reaches the VM as `RAISE`, but structured exception handlers are not yet compiled.
- The VM debugger API is available, while DAP remains interpreter-backed.
- VM embedding does not yet enforce the complete `PeaRuntime` capability model.
- Closure environments are snapshots, not shared lexical cells.
- Imports and default arguments remain interpreter-oriented.

## Next build

Version 0.22 should implement exception tables and handler unwinding, try/catch/finally compilation, shared closure cells, default parameter evaluation, bytecode module imports, import caching, and portable module source maps.

## Release requirement

Every future release must contain the cumulative changelog, detailed release notes, README, roadmap, version history, foundations, user and embedding guides, help pages, security and architecture notes, tests, examples, and an updated AI handover.




