# PeaLang v1.1.0 — Native Language Server Protocol

## Milestone: v1.1.0

### What was done
- Added `pealang/lsp.py` with standards-compliant LSP server over stdio
- Implemented: initialize, didOpen/didChange/didClose, hover, completion, definition, documentSymbol, publishDiagnostics, shutdown/exit
- Added `LSPServer` class and `build_lsp_namespace()`
- Registered in `analysis` and `stats`/`std.stats` namespaces
- Added `tests/test_lsp_v110.py` (6 tests)
- Added `docs/LSP.md` and `help/LSP.md`
- Version bumped to 1.1.0

### Test status
- 1019 tests passing

### Next steps (v1.2.0)
- Code formatter, linter, AST macros
- Extend `cli.py` and `tooling.py` with deterministic AST-based formatter
- Static dead-code/complexity linter
- Auto-fix codemods