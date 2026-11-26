# Formatter v3

Wave 3 continues with an additive formatter v3 layer. It does not change the
frozen 3.0 language surface, and it does not replace the existing `pea fmt`
command or `PeaFormatter`; both remain available.

`formatter_v3_capabilities()` returns the versioned capability set with the
default profile, available options, supported brace styles, comment preservation,
idempotence, and bytecode parity checking. `FORMATTER_V3_VERSION` records the
current release and `FORMATTER_V3_FORMAT` identifies the evidence format.

`FormatProfile` is a frozen, validated profile with `indent_size` from 1 to 8,
`max_line_length` at least 40, `brace_style` of `same_line` or `next_line`, and a
`newline_at_eof` flag. `DEFAULT_FORMAT_PROFILE` is stable and serializable.
Invalid profiles raise `FormatterV3Error` before any source is changed.

`format_source_v3()` normalizes line endings, recomputes brace-based indentation,
collapses whitespace outside strings, and normalizes operators, commas, colons,
braces, and comment spacing. Comment markers and string contents are detected
outside quoted regions and are preserved verbatim. Triple-quoted lines are not
rewritten. Blank-line runs are collapsed to at most one blank line, and a single
terminal newline is emitted when requested. Formatting intentionally does not
wrap long lines; `long_lines` records lines above `max_line_length` for review.

A `FormatResult` carries the version, format, profile, source name, change flag,
line count, long-line numbers, a unified diff with zero context, the formatted
text, parity evidence, an idempotence flag, and a stable digest. The digest
excludes the source name and original text, so identical formatted output yields
the same digest across host paths.

`verify_format_parity()` compiles original and formatted source to bytecode and
compares semantic fingerprints built from constants, code objects, parameters,
defaults, and operation/argument sequences. Source names and line positions are
excluded, so only semantic changes fail parity. Compilation errors are reported
as issues rather than raised.

`formatter_v3_report()` summarizes result count, changed count, per-result
evidence, and a stable digest. `formatter_v3_gate()` recomputes PASS/FAIL from
version, format, report state, digest shape, idempotence, and parity for every
result.

The `pea fmt-v3 PATH... [--check] [--write] [--indent N] [--max-line N]
[--brace-style same_line|next_line] [--emit FILE.json]` command reports changes
without writing by default. `--check` requires no changes, `--write` applies the
formatted source, and `--emit` writes the JSON report. `pea fmt-v3 --capabilities`
prints the versioned capability set. The `devx.formatter_v3` feature flag records
availability.
