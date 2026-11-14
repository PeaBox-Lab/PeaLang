# PeaLang v1.8.0 — Interactive Web Data IDE and reactive notebook server

## Milestone: v1.8.0

### What was done
- Added `pealang/notebook_ide.py` with reactive notebook and web IDE features
- `ReactiveCell`, `ReactiveNotebook` — reactive cell execution with dependency tracking
- `inspect_dataframe`, `inspect_sql_result` — visual SQL/DataFrame inspectors
- `publish_as_webapp` — one-click publishing of .pea scripts as interactive web apps
- `generate_notebook_html` — HTML notebook generation
- Registered in `analysis` and `stats`/`std.stats` namespaces
- Added `tests/test_notebook_ide_v180.py` (9 tests) and `tests/test_use_cases_v180.py` (1 test)
- Added `docs/NOTEBOOK_IDE.md` and `help/NOTEBOOK_IDE.md`
- Added `examples/use_cases/42_notebook_ide.pea`
- Version bumped to 1.8.0

### Test status
- 1085 tests passing

### Next steps (v1.9.0)
- Native FFI, plugin SDK, multi-language host bindings
- Host SDKs: Go SDK, Node.js/TypeScript Host SDK
- Bidirectional FFI with @pea_export
- OpenAPI/GraphQL importer