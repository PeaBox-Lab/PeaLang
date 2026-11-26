# WASM Backend

Wave 2 adds an optional WebAssembly backend for portable `.peac` bytecode. It is
a runtime facility, not a language feature: the frozen 3.0 surface defined by
`CORE_SURFACES` is unchanged.

`wasm_backend_supported()` qualifies a module by requiring the whole module to
use the Phase 72 fast-interpreter instruction set and every bytecode constant to
be representable in the backend IR as `null`, `int`, `float`, `bool`, or
`string`. Modules that do not qualify are executed by the standard virtual
machine without lowering.

`compile_wasm_backend()` lowers each supported instruction to a
`WasmBackendInstruction` with a stable operation name, JSON-friendly operand,
and source line. The resulting `WasmBackendModule` carries the format identifier
`pea-wasm-backend-v1`, a SHA-256 digest over the format, source name,
instructions, and constants, a standard WebAssembly v1 binary with two custom
sections, and a reviewable `.wat` text artifact. The manifest section records
format, backend version, ABI, source name, digest, support status, and
instruction count. The IR section records the instruction and constant tables.
`save(path)` writes the binary; `save_wat(path)` writes the text form;
`inspect_wasm_backend(data)` reads both sections back from bytes or a path and
rejects artifacts that are not WebAssembly v1 PeaLang backend modules.

`WasmBackendRuntime` executes the backend IR directly, routing `PRINT` through
the supplied output handler and enforcing the same global instruction limit as
the VM. Runtime results and output for supported modules must match the standard
VM. `verify_wasm_backend_parity()` runs both executors and requires identical
output and results; `benchmark_wasm_backend()` reports median wall-clock times
without asserting a speedup. `wasm_backend_report()` combines version, module
digest, artifact digest, format, instruction count, binary and WAT byte counts,
execution mode, output, result, and optional parity and benchmark data.
`wasm_backend_gate()` reduces that report to a PASS/FAIL result.

The `pea wasm-backend FILE.pea [--verify] [--benchmark] [--optimize] [--emit
FILE.wasm] [--wat FILE.wat]` command exposes the same behavior. With
`--optimize`, Phase 71's optimizer runs before lowering. The
`runtime.wasm_backend_v3` feature flag records availability.
