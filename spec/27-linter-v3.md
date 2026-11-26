# Linter v3

Wave 3 continues with an additive linter v3 layer. It does not change the frozen
3.0 language surface, and it does not replace the existing `pea lint` command or
`PeaLinter`; both remain available.

`linter_v3_capabilities()` returns the versioned capability set with the default
profile, the complete rule catalog, deterministic ordering, fix hints, and a
recomputed gate. `LINTER_V3_VERSION` records the current release and
`LINTER_V3_FORMAT` identifies the evidence format. Every rule has a stable code,
default severity, and name: `L301` line length, `L302` trailing whitespace,
`L303` TODO/FIXME marker, `L304` function naming, `L305` variable naming,
`L306` debug print, `L307` high complexity, `L308` unreachable code, and `L309`
parse error.

`LintProfileV3` is a frozen, validated profile with `max_line_length` at least
40, `max_complexity` at least 1, rule toggles for naming, complexity, dead code,
style, and debug prints, plus a `fail_on_warning` policy. Invalid profiles raise
`LinterV3Error` before any source is analyzed. `DEFAULT_LINT_PROFILE` is stable
and serializable.

`lint_source_v3()` normalizes line endings and returns reviewable evidence. Line
rules ignore marker text inside quoted strings and emit a fix hint for trailing
whitespace. AST rules use stable node kinds and source spans for naming, debug
print, complexity, unreachable statement, and parse-error findings. Diagnostics
are sorted by line, column, rule, severity, and message. A `LintDiagnosticV3`
fingerprint covers only rule, severity, message, position, and fix hint, so the
same finding hashes identically across host paths.

A `LintResultV3` carries the version, format, profile, source name, ordered
diagnostics, severity counts, a PASS/FAIL gate, and a stable digest. The digest
excludes the source name, wall-clock values, and raw paths. Errors always fail
the result gate; warnings fail it only when `fail_on_warning` is enabled.

`lint_v3_report()` summarizes result count, diagnostic count, severity counts,
per-result evidence, and a recomputable digest. `lint_v3_gate()` verifies the
version, format, gate shape, digest, profile, and per-result digest shape, then
recomputes the gate from the reported counts and warning policy. Extra fields
such as CLI decisions are ignored by digest recomputation.

The `pea lint-v3 PATH... [--check] [--emit FILE.json] [--max-line N]
[--max-complexity N] [--fail-on-warning]` command reports findings without
writing source. `--check` requires a passing gate, and `--emit` writes the JSON
report. `pea lint-v3 --capabilities` prints the versioned rule catalog. The
`devx.linter_v3` feature flag records availability.
