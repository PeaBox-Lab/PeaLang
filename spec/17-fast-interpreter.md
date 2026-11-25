# Fast interpreter

Wave 2 adds an optional direct-handler execution path for portable `.peac`
bytecode. It is a runtime facility, not a language feature: the frozen 3.0
surface defined by `CORE_SURFACES` is unchanged.

The fast path pre-binds each supported instruction to a closure and executes a
flat instruction stream with an explicit program counter. This avoids the
string-based dispatch chain used by the standard virtual machine for hot
straight-line scripts and small loops.

Supported operations are literal pushes (`CONST`, `NULL`, `TRUE`, `FALSE`),
variable access (`LOAD`, `STORE`), stack and output operations (`POP`, `PRINT`),
arithmetic and comparisons, unary `NEG` and `NOT`, and `JUMP`, `JUMP_IF_FALSE`,
and `HALT`. `fast_path_supported()` checks a whole module without executing it.
If any instruction is outside that set — including function definitions, calls,
imports, exception handlers, iterators, and object access — the entire module
runs on the standard virtual machine instead.

`FastInterpreter.run()` returns the same result as the virtual machine and
routes `PRINT` output to the configured callback. `verify_fast_parity()` runs
both executors and requires identical output and return values.
`benchmark_fast()` reports median wall-clock times for both paths.
`fast_interpreter_report()` combines mode, eligibility, output, digest,
optional parity, and optional benchmark data, and `fast_interpreter_gate()`
reduces that report to a PASS/FAIL result.

The `pea fast FILE.pea [--verify] [--benchmark] [--optimize]` command exposes
the same behavior. With `--optimize`, Phase 71's optimizer runs before the fast
path is compiled. The `runtime.fast_interpreter_v3` feature flag records
availability.
