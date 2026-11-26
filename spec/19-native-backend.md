# Native Backend

Wave 2 adds an optional native backend for portable `.peac` bytecode. It is a
runtime facility, not a language feature: the frozen 3.0 surface defined by
`CORE_SURFACES` is unchanged.

`native_supported()` qualifies a module by requiring the whole module to use the
Phase 72 fast-interpreter instruction set and every bytecode constant to be
representable in the native IR as `null`, `int`, `float`, `bool`, or `string`.
Modules that do not qualify are executed by the standard virtual machine
without lowering.

`compile_native()` lowers each supported instruction to a `NativeInstruction`
with a stable operation name, JSON-friendly operand, and source line. The
resulting `NativeModule` carries a format identifier (`pea-native-ir-v1`), a
SHA-256 digest over the format, source name, instructions, and constants, and a
self-contained C source artifact. `save(path)` writes that C source for host
compilation. The emitted C runtime implements the same value tags, arithmetic,
comparison, truthiness, print, load/store, and jump semantics as the bytecode VM.

`NativeRuntime` executes the native IR directly, routing `PRINT` through the
supplied output handler and enforcing the same global instruction limit as the
VM. Runtime results and output for supported modules must match the standard VM.
`verify_native_parity()` runs both executors and requires identical output and
results; `benchmark_native()` reports median wall-clock times without asserting
a speedup. `native_report()` combines version, module digest, artifact digest,
format, instruction count, source size, execution mode, output, result, and
optional parity and benchmark data. `native_gate()` reduces that report to a
PASS/FAIL result.

The `pea native FILE.pea [--verify] [--benchmark] [--optimize] [--emit FILE.c]`
command exposes the same behavior. With `--optimize`, Phase 71's optimizer runs
before lowering. The `runtime.native_backend_v3` feature flag records
availability.
