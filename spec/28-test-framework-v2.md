# Test framework v2

Wave 3 continues with an additive test framework v2 layer. It does not change
the frozen 3.0 language surface, and it does not replace the existing
`pea test` command or the native testing helpers; both remain available.

`test_framework_v2_capabilities()` returns the versioned capability set with
the default profile, supported options, the native VM executor, deterministic
ordering, stable case IDs, and a recomputed gate. `TEST_FRAMEWORK_V2_VERSION`
records the current release and `TEST_FRAMEWORK_V2_FORMAT` identifies the
evidence format.

`TestProfileV2` is a frozen, validated profile with a text `filter_text`, a
`fail_fast` switch, and a non-negative `max_failures` allowance. Invalid
profiles raise `TestFrameworkV2Error` before any test is executed.
`DEFAULT_TEST_PROFILE` is stable and serializable.

`run_test_source_v2()` normalizes line endings and runs native PeaLang tests
without exposing wall-clock elapsed time in its evidence. Each `TestCaseV2`
carries a stable ID derived from the describe block, test name, and source line,
plus a normalized error string that replaces the source name with `<source>`.
Cases are sorted by describe block, line, and name. When `fail_fast` is enabled,
execution evidence stops after the first failing case. When `filter_text` is
set, only case names containing that text are executed.

A `TestResultV2` carries the version, format, profile, source name, ordered
cases, passed and failed counts, a PASS/FAIL gate, and a stable digest. The
digest excludes source names, host paths, and elapsed timings. Failures always
produce a FAIL gate when they exceed `max_failures`; otherwise the gate is PASS.
A discovery error becomes one stable failing case so malformed test sources are
reported rather than raising out of the runner.

`test_v2_report()` summarizes result count, case count, passed and failed
counts, per-result evidence, and a recomputable digest. `test_v2_gate()` verifies
the version, format, gate shape, digest, profile, result digests, case
fingerprints, and count consistency, then recomputes the gate from the reported
failed count and warning policy. Extra fields such as CLI decisions are ignored
by digest recomputation.

The `pea test-v2 PATH... [--check] [--emit FILE.json] [--filter TEXT]
[--fail-fast] [--max-failures N]` command reports test evidence without changing
source. `--check` requires a passing gate, and `--emit` writes the JSON report.
`pea test-v2 --capabilities` prints the versioned capability set. The
`devx.test_framework_v2` feature flag records availability.
