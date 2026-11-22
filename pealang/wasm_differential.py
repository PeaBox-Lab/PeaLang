"""Cross-runtime differential fixtures and host capability ABI (roadmap 0.39).

This module closes the cross-runtime portability gap by:

* running a PeaLang program on the Python stack VM and again after a
  ``PEAC -> PEAWASM -> PEAC`` round trip, so serialization fidelity is proven
  on every fixture;
* describing the capability ABI that Node and browser hosts must implement
  when loading a ``PEAWASM`` artifact.

Nothing here requires a real WebAssembly engine: the ``PEAWASM`` artifact
embeds the portable PEAC bytecode in a custom section, so the same interpreter
can execute both sides of the differential and flag any lossy conversion.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .bytecode import BytecodeModule
from .compiler import compile_source_to_bytecode
from .vm import VirtualMachine
from .wasm import ABI_VERSION, WasmPolicy, compile_peac_to_wasm, inspect_wasm


#: Canonical host ABI. ``capability`` names match ``wasm_runtime.BROWSER_CAPABILITIES``.
HOST_ABI: dict[str, Any] = {
    "version": ABI_VERSION,
    "imports": {
        "pea_host_log": {"params": ["i32", "i32"], "results": [], "capability": "io"},
        "pea_host_fetch": {"params": ["i32", "i32"], "results": ["i32"], "capability": "network"},
        "pea_host_now": {"params": [], "results": ["i64"], "capability": "clock"},
    },
    "exports": {
        "pea_run": {"params": [], "results": ["i32"]},
        "pea_health": {"params": [], "results": ["i32"]},
    },
}

DEFAULT_POLICY = WasmPolicy()


def host_capability_abi(capabilities: list[str] | None = None) -> dict[str, Any]:
    """Return the host capability ABI, optionally filtered to ``capabilities``."""
    allowed = set(capabilities) if capabilities is not None else None
    imports = {
        name: dict(spec)
        for name, spec in HOST_ABI["imports"].items()
        if allowed is None or spec.get("capability") in allowed
    }
    return {
        "version": HOST_ABI["version"],
        "imports": imports,
        "exports": {name: dict(spec) for name, spec in HOST_ABI["exports"].items()},
        "policy": asdict(DEFAULT_POLICY),
    }


def validate_artifact_abi(artifact: Any) -> dict[str, Any]:
    """Check an artifact's imports/exports against the canonical host ABI.

    ``artifact`` may be a ``PEAWASM`` byte string, a path to one, or the dict
    returned by :func:`pealang.wasm.inspect_wasm`.
    """
    if isinstance(artifact, dict):
        manifest = artifact.get("manifest", artifact)
    else:
        manifest = inspect_wasm(artifact)["manifest"]
    known_imports = set(HOST_ABI["imports"])
    known_exports = set(HOST_ABI["exports"])
    imports = set(manifest.get("imports", []))
    exports = set(manifest.get("exports", []))
    return {
        "ok": imports <= known_imports and exports <= known_exports,
        "abi": manifest.get("abi"),
        "unknown_imports": sorted(imports - known_imports),
        "unknown_exports": sorted(exports - known_exports),
    }


def execute_peac(peac: dict[str, Any]) -> dict[str, Any]:
    """Execute a PEAC dictionary on the Python stack VM."""
    lines: list[Any] = []
    module = BytecodeModule.from_dict(peac)
    vm = VirtualMachine(output=lines.append)
    result = vm.run(module)
    return {"output": lines, "result": result}


def differential_run(source: str, source_name: str = "<input>",
                     policy: WasmPolicy | None = None) -> dict[str, Any]:
    """Run ``source`` directly and through a PEAC/PEAWASM round trip."""
    module = compile_source_to_bytecode(source, source_name)
    python_result = execute_peac(module.to_dict())

    artifact = compile_peac_to_wasm(module, policy=policy)
    raw = artifact.to_bytes()
    round_trip = inspect_wasm(raw)
    wasm_result = execute_peac(round_trip["peac"])
    manifest = round_trip["manifest"]

    return {
        "ok": python_result == wasm_result,
        "python": python_result,
        "wasm": wasm_result,
        "manifest": manifest,
        "artifact_size": len(raw),
        "abi": validate_artifact_abi(round_trip),
    }


def differential_fixtures() -> list[dict[str, Any]]:
    """Built-in fixtures covering arithmetic, strings, collections, loops and functions."""
    return [
        {"name": "arithmetic", "source": "print 2 + 3 * 4"},
        {"name": "strings", "source": 'print "pea" + "lang"'},
        {"name": "collections", "source": "let xs = [1, 2, 3]\nprint xs[1]\nprint len(xs)"},
        {"name": "loop", "source": "let total = 0\nfor i in [1, 2, 3] {\n  total = total + i\n}\nprint total"},
        {"name": "function", "source": "function add(a, b) {\n  return a + b\n}\nprint add(2, 5)"},
    ]


def run_differential_fixtures() -> dict[str, Any]:
    """Run every built-in differential fixture and summarise the outcome."""
    results = []
    for fixture in differential_fixtures():
        out = differential_run(fixture["source"], fixture["name"])
        results.append({
            "name": fixture["name"],
            "ok": out["ok"],
            "python_output": out["python"]["output"],
            "wasm_output": out["wasm"]["output"],
            "abi_ok": out["abi"]["ok"],
        })
    return {
        "ok": all(r["ok"] and r["abi_ok"] for r in results),
        "passed": sum(1 for r in results if r["ok"] and r["abi_ok"]),
        "total": len(results),
        "fixtures": results,
    }


def build_wasm_differential_namespace() -> dict[str, Any]:
    return {
        "HOST_ABI": HOST_ABI,
        "host_capability_abi": host_capability_abi,
        "validate_artifact_abi": validate_artifact_abi,
        "execute_peac": execute_peac,
        "differential_run": differential_run,
        "differential_fixtures": differential_fixtures,
        "run_differential_fixtures": run_differential_fixtures,
    }
