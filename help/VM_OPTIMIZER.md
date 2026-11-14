# Optimizing bytecode VM, JIT, and package hub (v2.0.0)

PeaLang provides VM optimization, bytecode v2, and package index management.

## Key functions

- `analysis.encode_bytecode_v2(instructions)` — encode bytecode
- `analysis.decode_bytecode_v2(data)` — decode bytecode
- `analysis.inspect_bytecode_v2(data)` — inspect bytecode
- `analysis.constant_fold(expr)` — constant folding
- `analysis.loop_unroll_hint(iterations, threshold)` — loop unrolling
- `analysis.benchmark_vm(source, iterations)` — benchmark
- `analysis.PackageIndex(index_dir)` — package index
- `analysis.OptimizationHints()` — optimization config