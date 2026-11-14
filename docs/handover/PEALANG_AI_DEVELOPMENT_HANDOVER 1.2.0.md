# PeaLang v1.2.0 — Code formatter, linter, and AST macros

## Milestone: v1.2.0

### What was done
- Added `pealang/formatter.py` with AST-based formatting, static linting, and auto-fix codemods
- `PeaFormatter`, `format_source_ast` — deterministic AST-based code formatter
- `PeaLinter`, `lint_source_ast` — static linter (dead code, complexity, naming, style)
- `codemod_remove_unused_imports`, `codemod_rename_variable`, `codemod_fix_naming` — auto-fix codemods
- Registered in `analysis` and `stats`/`std.stats` namespaces
- Added `tests/test_formatter_v120.py` (8 tests) and `tests/test_use_cases_v120.py` (1 test)
- Added `docs/FORMATTER.md` and `help/FORMATTER.md`
- Added `examples/use_cases/36_formatter.pea`
- Version bumped to 1.2.0

### Test status
- 1028 tests passing

### Next steps (v1.3.0)
- True standalone WASM bytecode VM
- Upgrade browser-sdk to execute compiled .peac bytecode in Web Worker
- Browser-native capability bridges (fetch, IndexedDB, localStorage, WebStreams)