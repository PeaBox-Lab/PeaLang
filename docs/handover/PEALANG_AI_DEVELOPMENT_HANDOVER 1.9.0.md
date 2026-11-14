# PeaLang v1.9.0 — Native FFI, plugin SDK, and multi-language host bindings

## Milestone: v1.9.0

### What was done
- Added `pealang/host_bindings.py` with bidirectional FFI, host SDK scaffolding, and OpenAPI importer
- `register_host_function` — register host functions as PeaLang builtins
- `generate_python_export`, `generate_typescript_export`, `generate_java_export` — export decorators
- `scaffold_go_sdk`, `scaffold_node_sdk` — host SDK scaffolding
- `import_openapi`, `generate_connector_package` — OpenAPI/GraphQL importer
- Registered in `analysis` and `stats`/`std.stats` namespaces
- Added `tests/test_host_bindings_v190.py` (9 tests) and `tests/test_use_cases_v190.py` (1 test)
- Added `docs/HOST_BINDINGS.md` and `help/HOST_BINDINGS.md`
- Added `examples/use_cases/43_host_bindings.pea`
- Version bumped to 1.9.0

### Test status
- 1095 tests passing

### Next steps (v2.0.0)
- Optimizing bytecode VM, JIT, package hub
- Inline caching, constant folding, loop unrolling
- Register-based bytecode format (.peac v2)
- Rust/Cython VM accelerator
- Decentralized package index with security scanning