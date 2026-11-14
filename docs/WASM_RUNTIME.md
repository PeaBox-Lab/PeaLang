# True standalone WASM bytecode VM (v1.3.0)

PeaLang provides enhanced WASM compilation and browser runtime support.

## Browser capability bridges

- `capability_bridge_source(capabilities)` — generate JS bridge code for browser capabilities
- `web_worker_runtime_source()` — generate Web Worker runtime for WASM execution
- `capability_sandbox_policy(capabilities)` — define capability sandbox policy
- `wasm_module_manifest(name, exports, imports, capabilities)` — generate WASM module manifest

## Browser capabilities

- `fetch` — HTTP fetch API
- `indexeddb` — IndexedDB storage
- `localstorage` — localStorage access
- `webstreams` — Web Streams API
- `console` — Console logging
- `crypto` — Web Crypto API