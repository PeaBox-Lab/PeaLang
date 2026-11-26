# Runtime Profiler

Wave 2 adds a deterministic bytecode profiler alongside the existing wall-clock
observability primitives. It does not change the frozen 3.0 language surface.

`RuntimeProfiler.run()` executes a `BytecodeModule` through a `VirtualMachine`
with an instrumentation hook that records three counter tables: opcode
execution counts, frame-name execution counts, and source-line hit counts.
`ProfileRun` carries the execution result, captured output, total instruction
count, sorted counter tables, and a SHA-256 digest over the format, module
digest, instruction count, and sorted counters. Wall-clock values are excluded
from the digest so repeated profiling of the same module yields reviewable,
stable evidence.

`profile_module()` returns a report with the module and profile digests, full
counter tables, configurable `top_opcodes`, `top_functions`, and `top_lines`
summaries, output, result, and a PASS gate marker. `verify_profile_parity()`
requires the profiled output and result to match a plain VM run.
`benchmark_profiler()` reports median VM and profiler wall-clock times and an
overhead ratio without asserting a performance threshold. `profiler_report()`
adds optional parity and benchmark evidence to the deterministic report, and
`profiler_gate()` reduces it to PASS/FAIL.

The `pea profiler FILE.pea [--verify] [--benchmark] [--top N] [--emit FILE.json]`
command exposes the same behavior. `--emit` writes the JSON report; `--optimize`
may be combined with the other options. The `runtime.profiler_v3` feature flag
records availability.
