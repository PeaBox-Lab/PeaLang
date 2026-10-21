# Changelog

## [0.9.0] - 2026-10-21
### Added
- `try / catch / finally` language-level exception handling.
- `throw` statement.
- Catch error objects with message/source/line/column fields.
- Default function parameters with required-before-default validation.
- Dedicated execution-model and running-program documentation.
### Changed
- Roadmap focus moved from AI/agent expansion to core language maturity and runtime usability.
- Function parameter AST now uses explicit parameter nodes supporting defaults.
### Compatibility
- v0.1-v0.8 capabilities remain available.
### Known limitations
- No named arguments, variadic arguments, multiline strings, optional/static types, namespace-isolated imports or stack-frame traceback yet.
- Formatter multiline/comment limitations remain.

## [0.8.0] - 2026-10-21
- Explicit agent/tool registry and per-agent tool-name allowlists.
## [0.7.0] - 2026-10-21
- Project manifests, local modules and path dependencies.
## [0.6.0] - 2026-10-21
- Provider-neutral AI workflows, structured outputs and portable skills.
## [0.5.0] - 2026-10-20
- Assertions, output fixtures, workflows, task helpers and bounded concurrency.
## [0.4.0] - 2026-10-20
- Formatter, checker, test runner, docs generator, richer REPL and comprehensive learning documentation.
## [0.3.0] - 2026-10-20
- Automation standard library and guarded processes.
## [0.2.0] - 2026-10-20
- Modular runtime, typed AST/spans, diagnostics, loop control, interpolation, mutation, imports, grammar and CI.
## [0.1.0] - Initial baseline
- Core interpreted language and CLI.
