# Changelog

## 0.13.0 - 2026-10-22
### Added
- Editor intelligence API for diagnostics, symbols, definitions, hover and completions.
- Experimental stdio JSON-RPC language server via `pea lsp`.
- VS Code extension starter for `.pea` files.
- Editor/LSP regression tests and documentation.
### Compatibility
- Runtime semantics and 0.12 lockfiles remain compatible.

## 0.12.0 - 2026-10-22
### Added
- Deterministic `pea.lock` generation.
- SHA-256 integrity capture for local dependency entry files.
- `pea lock` and `pea verify` commands.
- Lockfile tamper/change detection and tests.
### Compatibility
- `pea.json` format remains compatible with 0.11.0. Lockfiles are opt-in.

## 0.11.0 - 2026-10-22
### Added
- Structured error categories and Pea stack frames.
- Circular-import detection with import-chain messages.
- Manifest version and entry-point validation.
- Python packaging metadata, CI workflow, hardening tests, security guide, compatibility policy, and foundations documentation.
### Changed
- CLI errors use richer diagnostic rendering when available.
- Project manifests created by `pea init` now include `manifest_version: 1`.
### Compatibility
- Existing 0.10.0 syntax and public `execute`, `compile_source`, `Interpreter`, and `PeaError` exports remain supported.

## 0.10.0
AI service, tools, agents, skills, projects, module aliases/exports, exceptions, and expanded automation runtime.

## 0.1.0 - 0.9.x
Established lexer, parser, AST interpreter, collections, functions, control flow, module loading, formatter, checker, REPL, tests, standard namespaces, workflows, and bounded parallel expressions.
