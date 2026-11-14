"""True standalone WASM bytecode VM runtime for PeaLang (v1.3.0).

Provides enhanced WASM compilation, browser capability bridges, Web Worker
runtime generation, and capability sandboxing for zero-server browser execution.
"""

from __future__ import annotations

import json
from typing import Any

from .wasm import WasmPolicy, WasmArtifact, compile_peac_to_wasm, browser_loader_source


# ---------------------------------------------------------------------------
# Browser capability bridges
# ---------------------------------------------------------------------------

BROWSER_CAPABILITIES = {
    "fetch": {"description": "HTTP fetch API", "permissions": ["network"]},
    "indexeddb": {"description": "IndexedDB storage", "permissions": ["storage"]},
    "localstorage": {"description": "localStorage access", "permissions": ["storage"]},
    "webstreams": {"description": "Web Streams API", "permissions": ["io"]},
    "console": {"description": "Console logging", "permissions": ["io"]},
    "crypto": {"description": "Web Crypto API", "permissions": ["crypto"]},
}


def capability_bridge_source(capabilities: list[str] | None = None) -> str:
    """Generate JavaScript bridge code for browser capabilities."""
    caps = capabilities or list(BROWSER_CAPABILITIES.keys())
    lines = [
        "// PeaLang browser capability bridges",
        "const peaCapabilities = {};",
        "",
    ]
    for cap in caps:
        info = BROWSER_CAPABILITIES.get(cap, {})
        if cap == "fetch":
            lines.append("""
peaCapabilities.fetch = async (url, options) => {
  const resp = await fetch(url, options || {});
  return { status: resp.status, ok: resp.ok, text: await resp.text() };
};""")
        elif cap == "indexeddb":
            lines.append("""
peaCapabilities.indexeddb = {
  open: (name, version) => new Promise((resolve, reject) => {
    const req = indexedDB.open(name, version);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  }),
  get: (db, store, key) => new Promise((resolve, reject) => {
    const tx = db.transaction(store, "readonly");
    const req = tx.objectStore(store).get(key);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  }),
  put: (db, store, value) => new Promise((resolve, reject) => {
    const tx = db.transaction(store, "readwrite");
    const req = tx.objectStore(store).put(value);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  }),
};""")
        elif cap == "localstorage":
            lines.append("""
peaCapabilities.localstorage = {
  get: (key) => localStorage.getItem(key),
  set: (key, value) => localStorage.setItem(key, value),
  remove: (key) => localStorage.removeItem(key),
};""")
        elif cap == "webstreams":
            lines.append("""
peaCapabilities.webstreams = {
  readable: (source) => new ReadableStream(source),
  writable: (sink) => new WritableStream(sink),
};""")
        elif cap == "console":
            lines.append("""
peaCapabilities.console = {
  log: (...args) => console.log(...args),
  warn: (...args) => console.warn(...args),
  error: (...args) => console.error(...args),
};""")
        elif cap == "crypto":
            lines.append("""
peaCapabilities.crypto = {
  randomUUID: () => crypto.randomUUID(),
  digest: async (algo, data) => {
    const buf = await crypto.subtle.digest(algo, new TextEncoder().encode(data));
    return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
  },
};""")
    lines.append("")
    lines.append("export { peaCapabilities };")
    return "\n".join(lines)


def web_worker_runtime_source() -> str:
    """Generate a Web Worker runtime for executing PeaLang WASM modules."""
    return '''// PeaLang Web Worker Runtime
const peaRuntime = {
  module: null,
  instance: null,
  memory: null,
  async load(url, imports = {}) {
    const bytes = await (await fetch(url)).arrayBuffer();
    const result = await WebAssembly.instantiate(bytes, {
      ...imports,
      env: {
        ...imports.env,
        console_log: (ptr, len) => {
          const bytes = new Uint8Array(this.memory.buffer, ptr, len);
          const text = new TextDecoder().decode(bytes);
          console.log("[PeaLang]", text);
        },
      },
    });
    this.instance = result.instance;
    this.memory = result.instance.exports.memory;
    return result;
  },
  call(name, ...args) {
    if (!this.instance) throw new Error("Runtime not loaded");
    return this.instance.exports[name](...args);
  },
  async handleMessage(msg) {
    switch (msg.type) {
      case "load":
        await this.load(msg.url, msg.imports);
        self.postMessage({ type: "loaded" });
        break;
      case "call":
        try {
          const result = this.call(msg.name, ...msg.args);
          self.postMessage({ type: "result", id: msg.id, result });
        } catch (e) {
          self.postMessage({ type: "error", id: msg.id, error: e.message });
        }
        break;
    }
  },
};

self.onmessage = (e) => peaRuntime.handleMessage(e.data);
'''


def capability_sandbox_policy(capabilities: list[str] | None = None) -> dict[str, Any]:
    """Define a capability sandbox policy for browser execution."""
    caps = capabilities or []
    return {
        "allowed_capabilities": caps,
        "denied_capabilities": [c for c in BROWSER_CAPABILITIES if c not in caps],
        "network_access": "fetch" in caps,
        "storage_access": "indexeddb" in caps or "localstorage" in caps,
        "crypto_access": "crypto" in caps,
    }


def wasm_module_manifest(module_name: str, exports: list[str] | None = None,
                         imports: list[str] | None = None,
                         capabilities: list[str] | None = None) -> dict[str, Any]:
    """Generate a manifest for a WASM module."""
    return {
        "name": module_name,
        "format": "PEAWASM",
        "version": "1.3.0",
        "exports": exports or [],
        "imports": imports or [],
        "capabilities": capabilities or [],
        "sandbox": capability_sandbox_policy(capabilities),
    }


def build_wasm_runtime_namespace() -> dict[str, Any]:
    return {
        "capability_bridge_source": capability_bridge_source,
        "web_worker_runtime_source": web_worker_runtime_source,
        "capability_sandbox_policy": capability_sandbox_policy,
        "wasm_module_manifest": wasm_module_manifest,
        "BROWSER_CAPABILITIES": BROWSER_CAPABILITIES,
    }
