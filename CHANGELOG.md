# Changelog
## [0.3.0] - 2026-10-20
### Added
- `file`, `path`, `json`, `csv`, `env`, `datetime`, `regex`, `http`, and guarded `process` namespaces.
- Structured HTTP response dictionaries and JSON decoding helper.
- Explicit `--allow-process` CLI safety gate.
- Automation examples, standard-library reference, security model, tests and v0.3 handover.
### Changed
- Preferred standard-library APIs are namespaced; v0.1 flat built-ins remain for compatibility.
- Runtime `execute` and `Interpreter` accept `allow_process=False`.

## [0.2.0] - 2026-10-20
- Modular runtime, typed AST/source spans, diagnostics, break/continue, interpolation, property/index assignment, import foundation, grammar, CI and expanded tests.

## [0.1.0] - Initial baseline
- First working interpreter: variables/constants, expressions, control flow, functions, collections, files, REPL and CLI.
