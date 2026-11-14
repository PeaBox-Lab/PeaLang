"""Regression coverage for v1.3.0 WASM runtime."""

from pealang.wasm_runtime import (
    build_wasm_runtime_namespace,
    capability_bridge_source,
    web_worker_runtime_source,
    capability_sandbox_policy,
    wasm_module_manifest,
    BROWSER_CAPABILITIES,
)


def test_capability_bridge_source():
    src = capability_bridge_source(["fetch", "console"])
    assert "peaCapabilities" in src
    assert "fetch" in src
    assert "console" in src


def test_web_worker_runtime_source():
    src = web_worker_runtime_source()
    assert "PeaLang Web Worker Runtime" in src
    assert "onmessage" in src
    assert "WebAssembly" in src


def test_capability_sandbox_policy():
    policy = capability_sandbox_policy(["fetch", "crypto"])
    assert policy["network_access"] is True
    assert policy["crypto_access"] is True
    assert policy["storage_access"] is False
    assert "indexeddb" in policy["denied_capabilities"]


def test_wasm_module_manifest():
    manifest = wasm_module_manifest("my_module", exports=["main"], capabilities=["fetch"])
    assert manifest["name"] == "my_module"
    assert manifest["format"] == "PEAWASM"
    assert manifest["version"] == "1.3.0"
    assert "fetch" in manifest["capabilities"]
    assert manifest["sandbox"]["network_access"] is True


def test_browser_capabilities():
    assert "fetch" in BROWSER_CAPABILITIES
    assert "indexeddb" in BROWSER_CAPABILITIES
    assert "localstorage" in BROWSER_CAPABILITIES


def test_build_wasm_runtime_namespace():
    ns = build_wasm_runtime_namespace()
    assert "capability_bridge_source" in ns
    assert "web_worker_runtime_source" in ns
    assert "capability_sandbox_policy" in ns
    assert "wasm_module_manifest" in ns
    assert "BROWSER_CAPABILITIES" in ns
    assert len(ns) == 5
