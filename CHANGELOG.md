# Changelog
All notable changes are documented here.

## [0.2.0] - 2026-10-20
### Added
- Typed dataclass AST with source spans.
- `break` and `continue` with loop-context validation.
- String interpolation with expressions and escaped braces.
- Dictionary property access and property assignment.
- List/dictionary indexed assignment and compound indexed assignment.
- Local quoted-file imports, resolved relative to the entry file.
- Source-aware lexer, parser, and runtime diagnostics.
- Undefined-name suggestions.
- Formal EBNF grammar, CI matrix, packaging metadata and expanded examples/tests.

### Changed
- Split the original single-file runtime into lexer, parser, AST, environment, interpreter, errors, and compatibility facade modules.
- `pea` is the preferred CLI; `pealang` remains available.

### Compatibility
- Existing v0.1 variables, constants, expressions, conditions, loops, functions, recursion, collections, file operations, REPL, CLI, and public Python imports are retained.

## [0.1.0] - Initial baseline
- First working Python tree-walk interpreter.
- Variables/constants, expressions, conditions, loops, functions/recursion, lists/dictionaries, built-ins, files, REPL and CLI.
