# PeaLang v1.3.0 — True standalone WASM bytecode VM

## Milestone: v1.3.0

### What was done
- Added `pealang/wasm_runtime.py` with browser capability bridges, Web Worker runtime, and sandboxing
- `capability_bridge_source` — generate JS bridge code for browser capabilities (fetch, IndexedDB, localStorage, WebStreams, console, crypto)
- `web_worker_runtime_source` — generate Web Worker runtime for WASM execution
- `capability_sandbox_policy` — define capability sandbox policy
- `wasm_module_manifest` — generate WASM module manifest
- `BROWSER_CAPABILITIES` — capability definitions
- Registered in `analysis` and `stats`/`std.stats` namespaces
- Added `tests/test_wasm_runtime_v130.py` (6 tests) and `tests/test_use_cases_v130.py` (1 test)
- Added `docs/WASM_RUNTIME.md` and `help/WASM_RUNTIME.md`
- Added `examples/use_cases/37_wasm_runtime.pea`
- Version bumped to 1.3.0

### Test status
- 1035 tests passing

### Next steps (v1.4.0)
- Reactive react-sdk with custom hooks (usePeaScript, usePeaDataFrame, usePeaQuery, usePeaValidation)
- Zero-copy TypedArray/JSON adapters for frontend table engines
- Sub-millisecond reactive filtering and sorting