# PeaLang v2.0.0 — Optimizing bytecode VM, JIT, and package hub

## Milestone: v2.0.0

### What was done
- Added `pealang/vm_optimizer.py` with VM optimization and package index management
- `OptimizationHints` — optimization configuration (constant folding, inline caching, loop unrolling, dead code elimination, strength reduction)
- `constant_fold` — constant folding for simple expressions
- `loop_unroll_hint` — loop unrolling suggestions
- `encode_bytecode_v2`, `decode_bytecode_v2`, `inspect_bytecode_v2` — register-based bytecode format v2 with checksum validation
- `benchmark_vm`, `benchmark_compare` — performance benchmarking
- `PackageIndex` — decentralized package index with publish/resolve/search/security scan
- Registered in `analysis` and `stats`/`std.stats` namespaces
- Added `tests/test_vm_optimizer_v200.py` (11 tests) and `tests/test_use_cases_v200.py` (1 test)
- Added `docs/VM_OPTIMIZER.md` and `help/VM_OPTIMIZER.md`
- Added `examples/use_cases/44_vm_optimizer.pea`
- Version bumped to 2.0.0

### Test status
- 1107 tests passing

### Roadmap complete
All phases from v1.0 to v2.0 have been implemented:
- v1.0.0 GA — Core stabilization & public API lock
- v1.1.0 — Native LSP server
- v1.2.0 — Code formatter, linter, AST macros
- v1.3.0 — True standalone WASM bytecode VM
- v1.4.0 — Reactive React SDK + browser data grid
- v1.5.0 — Full-stack web server + auto-typed SDK generator
- v1.6.0 — Arrow/DuckDB vectorized DataFrame backend
- v1.7.0 — ONNX model export + vector/RAG primitives
- v1.8.0 — Interactive Web Data IDE + reactive notebook server
- v1.9.0 — Native FFI, plugin SDK, multi-language host bindings
- v2.0.0 — Optimizing bytecode VM, JIT, package hub