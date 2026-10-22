# PeaLang 0.30.0 Release Notes

PeaLang 0.30 is a production-hardening release focused on observability, profiling, benchmarking, conformance, and release integrity.

## Added

- VM `Profiler` with instruction, opcode, function, and elapsed-time statistics.
- Source-line `Coverage` collection.
- Transport-neutral `Observer` and `TraceEvent` observability API.
- `MemoryObserver` reference implementation.
- VM instrumentation hook independent from debugger hooks.
- `pea profile` command.
- `pea benchmark` command with min/median/mean/max statistics.
- Benchmark corpus foundation under `benchmarks/`.
- Interpreter-versus-VM differential conformance test.
- Source inventory/hash comparison utilities.
- Mandatory no-unintentional-removal release gate.
- Release manifest and integrity report.

## Compatibility

Instrumentation is opt-in and does not alter ordinary VM execution. Existing Python, FastAPI, Java, TypeScript, React, package-manager, sync VM, and async VM interfaces remain available.
