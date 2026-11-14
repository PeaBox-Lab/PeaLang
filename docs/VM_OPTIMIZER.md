# Optimizing bytecode VM, JIT, and package hub (v2.0.0)

PeaLang provides VM optimization, bytecode v2, and package index management.

## Bytecode v2

- `encode_bytecode_v2(instructions)` — encode to register-based format
- `decode_bytecode_v2(data)` — decode bytecode v2
- `inspect_bytecode_v2(data)` — inspect bytecode metadata

## VM optimization

- `OptimizationHints()` — optimization configuration
- `constant_fold(expr)` — constant folding
- `loop_unroll_hint(iterations, threshold)` — loop unrolling hint
- `benchmark_vm(source, iterations)` — benchmark VM execution
- `benchmark_compare(source, iterations)` — compare with/without optimizations

## Package index

- `PackageIndex(index_dir)` — decentralized package index
- `.publish(name, version, metadata)` — publish package
- `.resolve(name, version)` — resolve package version
- `.search(query)` — search packages
- `.list_packages()` — list all packages
- `.remove(name)` — remove package
- `.security_scan(name)` — security scan