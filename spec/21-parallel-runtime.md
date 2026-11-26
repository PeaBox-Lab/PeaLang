# Parallel Runtime

Wave 2 adds an optional bounded parallel runtime for independent bytecode
tasks. It is a runtime facility, not a language feature: the frozen 3.0 surface
defined by `CORE_SURFACES` is unchanged.

A `ParallelTask` pairs a `BytecodeModule` with an isolated global environment.
`build_parallel_plan()` produces a deterministic task summary and SHA-256 digest
covering the format, support status, task names, module digests, globals, and
instruction counts. Planning never executes bytecode.

`parallel_supported()` qualifies a task set when every task carries a
`BytecodeModule` and no module code or function body uses `AWAIT` or `IMPORT`.
Qualified task sets run in a `ThreadPoolExecutor` bounded by the configured
worker count; each worker receives a private `VirtualMachine` and a copy of the
task globals. Unqualified sets, or a worker count of one, run sequentially on
the standard VM. Worker completion order is never published: results, outputs,
and instruction counts are returned in task order.

`verify_parallel_parity()` runs the sequential and parallel executors and
requires identical per-task output and results. `benchmark_parallel()` reports
median wall-clock times without asserting a speedup. `parallel_report()` combines
version, format, plan digest, support status, execution mode, active workers,
task count, ordered results and outputs, instruction counts, and optional parity
and benchmark data. `parallel_gate()` reduces that report to PASS/FAIL.

The `pea parallel FILE.pea [--verify] [--benchmark] [--tasks N] [--workers N]`
command exposes the same behavior. `--tasks` creates isolated copies of the
module with a `task_id` global; `--optimize` may be combined with the other
options. The `runtime.parallel_runtime_v3` feature flag records availability.
