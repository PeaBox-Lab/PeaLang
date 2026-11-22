"""Cross-runtime portability tests (roadmap 0.39)."""

from pealang import analysis
from pealang.wasm import WasmPolicy, compile_peac_to_wasm
from pealang.compiler import compile_source_to_bytecode
from pealang.wasm_differential import (
    HOST_ABI,
    build_wasm_differential_namespace,
    differential_fixtures,
    differential_run,
    execute_peac,
    host_capability_abi,
    run_differential_fixtures,
    validate_artifact_abi,
)


def test_host_capability_abi_full():
    abi = host_capability_abi()
    assert abi["version"] == HOST_ABI["version"]
    assert set(abi["imports"]) == set(HOST_ABI["imports"])
    assert set(abi["exports"]) == set(HOST_ABI["exports"])
    assert abi["policy"]["allow_network"] is False


def test_host_capability_abi_filtered():
    abi = host_capability_abi(["io"])
    assert list(abi["imports"]) == ["pea_host_log"]
    assert "pea_host_fetch" not in abi["imports"]


def test_differential_fixtures_all_pass():
    report = run_differential_fixtures()
    assert report["ok"] is True
    assert report["passed"] == report["total"] == len(differential_fixtures())
    for fixture in report["fixtures"]:
        assert fixture["python_output"] == fixture["wasm_output"]
        assert fixture["abi_ok"] is True


def test_differential_run_arithmetic():
    out = differential_run("print 2 + 3 * 4", "arith")
    assert out["ok"] is True
    assert out["python"] == out["wasm"]
    assert out["python"]["output"] == [14]
    assert out["manifest"]["format"] == "PEAWASM"
    assert out["abi"]["ok"] is True


def test_execute_peac_matches_compiler():
    module = compile_source_to_bytecode("print 6 * 7", "mul")
    assert execute_peac(module.to_dict())["output"] == [42]


def test_validate_artifact_abi_ok():
    module = compile_source_to_bytecode("print 1", "one")
    raw = compile_peac_to_wasm(module, policy=WasmPolicy()).to_bytes()
    report = validate_artifact_abi(raw)
    assert report["ok"] is True
    assert report["unknown_imports"] == []
    assert report["unknown_exports"] == []


def test_validate_artifact_abi_unknown_symbols():
    report = validate_artifact_abi({
        "manifest": {
            "abi": HOST_ABI["version"],
            "imports": ["pea_host_log", "pea_host_mystery"],
            "exports": ["pea_run", "pea_extra"],
        }
    })
    assert report["ok"] is False
    assert report["unknown_imports"] == ["pea_host_mystery"]
    assert report["unknown_exports"] == ["pea_extra"]


def test_analysis_namespace_exposes_differential_api():
    ns = analysis.build_analysis_namespace()
    for key in ("host_capability_abi", "differential_run",
                "run_differential_fixtures", "wasm_differential"):
        assert key in ns
    namespace = ns["wasm_differential"]()
    assert namespace["HOST_ABI"] == HOST_ABI


def test_build_wasm_differential_namespace_keys():
    ns = build_wasm_differential_namespace()
    assert "host_capability_abi" in ns
    assert "differential_run" in ns
    assert ns["run_differential_fixtures"]()["ok"] is True
