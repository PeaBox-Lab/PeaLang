# Conformance suite

The v2 conformance suite is a curated, deterministic set of portable language
cases. It complements, and does not replace, the generated differential and
fuzz harness in `pealang.conformance`.

A `ConformanceCaseV2` declares an identifier, name, category, kind, source, and
either expected output or expected diagnostic codes. Four kinds are defined:

- `runtime` — the source must produce identical normalized output on the
  interpreter and the bytecode VM.
- `macro` — the source is expanded with the case's safe macro expander and then
  executed on the bytecode VM.
- `static` — the combined semantic and resource-scope analysis must report all
  declared diagnostic codes.
- `module` — the source is written to a temporary project and analyzed, so
  cross-file diagnostics such as `M201` are available.

Output normalization stringifies booleans as `true`/`false` and serializes
lists and maps as deterministic JSON. This keeps interpreter output, which is
stringified, comparable with VM output, which is raw.

`run_conformance_suite_v2()` returns a stable report with the suite version,
case count, pass/fail counts, definition issues, per-runtime execution counts,
and one result record per case. `conformance_report_v2()` wraps that report for
CLI output, and `conformance_gate_v2()` reduces it to `PASS` or `FAIL`.
`pea conformance-v2` prints the report as JSON and exits zero only when the
gate passes.
