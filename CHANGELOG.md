# Changelog

## [0.4.0] - 2026-10-20
### Added
- Canonical `pea fmt` formatter with recursive discovery and CI check mode.
- `pea check` static checker with P100, P101, P102 and P104 diagnostics.
- `pea test` language-level smoke/integration runner.
- `pea docs` Markdown API generator for public functions.
- Consolidated `run`, `repl`, `fmt`, `check`, `test`, and `docs` CLI commands.
- REPL `:help`, `:vars`, and `:clear` commands.
- Dedicated language basics, foundations, tooling, CLI, formatter, checker and test help documentation.
- Developer-tooling tests and a PeaLang smoke-test directory.
### Changed
- Version updated to 0.4.0.
- Direct `pea file.pea` execution remains compatible while `pea run file.pea` is now explicit.
- README and guides reorganized around a learn-build-check-test workflow.
### Known limitations
- Formatter does not preserve comments in v0.4.
- Checker is not a type checker and does not resolve imported declarations.
- Pea test runner treats successful execution as pass and has no native assertion syntax yet.
- API docs do not extract doc comments yet.

## [0.3.0] - 2026-10-20
### Added
- Namespaced `file`, `path`, `json`, `csv`, `env`, `datetime`, `regex`, `http`, and guarded `process` automation APIs.
- Structured HTTP responses and process opt-in through `--allow-process`.
### Changed
- Namespaced APIs became preferred while compatible flat built-ins remained.

## [0.2.0] - 2026-10-20
### Added
- Typed AST and source spans, modular runtime, diagnostics, break/continue, interpolation, property access, indexed/property assignment, local imports, formal grammar and CI.

## [0.1.0] - Initial baseline
### Added
- Variables/constants, expressions, conditions, loops, functions/recursion, lists/dictionaries, file operations, built-ins, REPL and CLI.
