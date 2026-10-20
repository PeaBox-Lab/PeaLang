# PeaLang v0.4.0 Release Notes

v0.4.0 makes PeaLang easier to learn, maintain and use in real projects. The release adds a coherent developer workflow: write, format, check, test, document and run.

## Major additions
- `pea fmt` for stable formatting and CI verification
- `pea check` for early diagnostics
- `pea test` for executable language-level scenarios
- `pea docs` for Markdown function references
- richer persistent REPL commands
- dedicated basics and foundations learning material

## Compatibility
The complete v0.1-v0.3 behavior remains covered by regression tests. Direct execution remains supported. No language grammar feature was intentionally removed.

## Validation and boundaries
See `TEST_REPORT.md`. The formatter's comment preservation, cross-file checker resolution, native assertion syntax and doc-comment extraction remain planned enhancements rather than completed features.
