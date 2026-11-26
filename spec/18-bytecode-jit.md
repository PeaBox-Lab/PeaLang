# Bytecode JIT

Wave 2 adds an optional, profile-guided trace JIT for portable `.peac`
bytecode. It is a runtime facility, not a language feature: the frozen 3.0
surface defined by `CORE_SURFACES` is unchanged.

`profile_execution()` runs the module once on a non-emitting instrumented
version of the Phase 72 fast path and records an instruction count for every
bytecode offset. A profile is supported only when the whole module uses the
fast-interpreter instruction set and the profiling run completes within the
instruction limit. Profiling never emits program output.

`select_traces()` inspects backward `JUMP` instructions. A back-edge becomes a
`HotTrace` when its execution count reaches the threshold and every instruction
in the loop body is supported by the fast path. Traces are ordered by descending
hit count and capped at four by default.

`compile_trace()` pre-binds each instruction in the selected range. The integer
forms of `ADD`, `SUB`, and `MUL` are replaced with guarded handlers that require
both operands to have exact type `int`. When a guard fails, `JITDeopt` is raised;
`JITRuntime` catches it, executes the instruction with the standard fast-path
handler, and continues. A bounded step budget prevents a single trace from
monopolizing execution, and the global VM instruction limit is enforced inside
traces as well.

Modules that are not eligible for the fast path run entirely on the standard
virtual machine. In that case the report mode is `vm`, and no behavioral change
is possible.

`verify_jit_parity()` runs both the standard VM and the JIT runtime and requires
identical output and results. `benchmark_jit()` reports median wall-clock times
for both paths without asserting a speedup. `bytecode_jit_report()` combines
version, module digest, threshold, profile summary, traces, compiled-trace
counts, runtime statistics, output, result, optional parity, and optional
benchmark data. `bytecode_jit_gate()` reduces that report to a PASS/FAIL result.

The `pea jit FILE.pea [--verify] [--benchmark] [--optimize] [--threshold N]`
command exposes the same behavior. With `--optimize`, Phase 71's optimizer runs
before profiling. The `runtime.bytecode_jit_v3` feature flag records
availability.
