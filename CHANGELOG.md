# Changelog

## [0.10.0] - 2026-10-21
### Added
- `import "module.pea" as alias` namespace imports.
- Explicit `export symbol` module visibility.
- Isolated child environments for aliased modules.
- Checker diagnostic P105 for exporting an undefined symbol.
- Modules/namespaces guide, examples and tests.
### Compatibility
- Historical unaliased imports retain shared-global behaviour.
### Known limitations
- No `from` imports, automatic aliases, wildcard export, circular-module diagnostics or package registry.
- Formatter multiline/comment limitations remain.

## [0.9.0] - 2026-10-21
- try/catch/finally, throw, default function parameters and interpreter execution documentation.
## [0.8.0] - 2026-10-21
- Agent/tool foundations with explicit allowlists.
## [0.7.0] - 2026-10-21
- Project manifests, local modules and path dependencies.
## [0.6.0] - 2026-10-21
- Provider-neutral AI workflows and portable skills.
## [0.5.0] - 2026-10-20
- Assertions, output fixtures, workflows and bounded concurrency.
## [0.4.0] - 2026-10-20
- Developer tooling and comprehensive learning documentation.
## [0.3.0] - 2026-10-20
- Automation standard library.
## [0.2.0] - 2026-10-20
- Modular runtime/language foundations.
## [0.1.0] - Initial interpreter.
