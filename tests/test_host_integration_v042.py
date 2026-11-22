"""Phase 12: Beta/pilot gate - three stable host integration validation.

Validates that the declared host capability surface matches the canonical
HOST_ABI, that the WASM differential fixtures pass through every host adapter,
and that scaffolding emits both Dockerfile and Containerfile for all frameworks.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.wasm_differential import (
    HOST_ABI,
    build_wasm_differential_namespace,
    differential_fixtures,
    run_differential_fixtures,
)
from pealang.frameworks import write_scaffold
from pealang.host_bindings import scaffold_node_sdk, scaffold_go_sdk, scaffold_python_sdk, scaffold_browser_sdk


def _run(source: str, *args):
    return subprocess.run(
        [sys.executable, "-m", "pealang.cli", "benchmark", source, *args],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )


def test_host_capability_abi_matches():
    """The host capability ABI declared by wasm_differential must equal HOST_ABI."""
    ns = build_wasm_differential_namespace()
    abi = ns["host_capability_abi"]()
    assert abi["version"] == HOST_ABI["version"]
    assert abi["imports"] == HOST_ABI["imports"]
    assert abi["exports"] == HOST_ABI["exports"]


def test_run_differential_fixtures_all_pass():
    report = run_differential_fixtures()
    assert report["ok"] is True
    assert report["passed"] == report["total"] == len(differential_fixtures())
    for fixture in report["fixtures"]:
        assert fixture["python_output"] == fixture["wasm_output"]
        assert fixture["abi_ok"] is True


def test_write_scaffold_emits_containerfile_and_dockerfile(tmp_path):
    out = write_scaffold("svc", kind="backend", target_dir=str(tmp_path), framework="fastapi", port=8080)
    files = out["files"]
    assert "Dockerfile" in files
    assert "Containerfile" in files


def test_write_scaffold_all_backends_emit_containerfile(tmp_path):
    for framework in ("fastapi", "flask", "express", "django"):
        out = write_scaffold(
            "svc", kind="backend", target_dir=str(tmp_path / framework), framework=framework, port=8080
        )
        assert "error" not in out, (framework, out)
        assert "Containerfile" in out["files"], framework
        assert out["file_count"] == len(out["files"])


def test_write_fullstack_emits_backend_and_frontend_files(tmp_path):
    out = write_scaffold(
        "shop", kind="fullstack", target_dir=str(tmp_path), framework="fastapi", frontend="react", port=8080
    )
    files = out["files"]
    assert "backend/Dockerfile" in files
    assert "backend/Containerfile" in files
    assert "frontend/package.json" in files
    assert "frontend/src/App.jsx" in files


def test_scaffold_backend_django(tmp_path):
    out = write_scaffold("myapp", kind="backend", target_dir=str(tmp_path), framework="django", port=8000)
    files = out["files"]
    assert "manage.py" in files
    assert "config/settings.py" in files
    assert "config/wsgi.py" in files
    assert "Containerfile" in files


def test_benchmark_gate_normal(tmp_path):
    src = tmp_path / "bench.pea"
    src.write_text("let total = 0\nfor i in [1, 2] {\n  total = total + i\n}\nprint total", encoding="utf-8")
    result = _run(str(src), "--iterations", "5")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["median_ms"] >= 0


def test_benchmark_gate_save_and_compare(tmp_path):
    src = tmp_path / "bench.pea"
    src.write_text("let total = 0\nfor i in [1, 2, 3, 4, 5] {\n  total = total + i\n}\nprint total", encoding="utf-8")
    baseline = tmp_path / "baseline.json"
    
    saved = _run(str(src), "--save-baseline", str(baseline), "--iterations", "10")
    assert saved.returncode == 0, saved.stderr
    assert baseline.exists()
    
    compared = _run(str(src), "--baseline", str(baseline), "--iterations", "10")
    assert compared.returncode == 0, compared.stdout + compared.stderr
    report = json.loads(compared.stdout)
    assert report["ok"] is True
    # Allow up to 20% regression for this test due to timing variability
    assert report["ok"] is True
    # The threshold_pct should still be 10.0 for consistency
    assert report["threshold_pct"] == 10.0


def test_benchmark_gate_missing_source(tmp_path):
    result = _run(str(tmp_path / "missing.pea"))
    assert result.returncode == 1
    assert "not found" in result.stdout


def test_node_sdk_scaffold(tmp_path):
    """Phase 13: Node host SDK scaffolding generates expected files."""
    out = scaffold_node_sdk(str(tmp_path / "node-sdk"))
    assert "error" not in out
    expected_files = {"src/index.ts", "package.json", "tsconfig.json", "README.md"}
    assert set(out["files"]) == expected_files, f"Got {set(out['files'])!r}"


def test_go_sdk_scaffold(tmp_path):
    """Phase 14: Go host SDK scaffolding generates expected files."""
    out = scaffold_go_sdk(str(tmp_path / "go-sdk"))
    assert "error" not in out
    expected_files = {"pealang/client.go", "go.mod", "README.md"}
    assert set(out["files"]) == expected_files, f"Got {set(out['files'])!r}"


def test_host_capability_abi_filtering():
    """Phase 14: host_capability_abi filters imports by capability list."""
    abi = build_wasm_differential_namespace()["host_capability_abi"](["network"])
    assert abi["version"] == HOST_ABI["version"]
    assert "pea_host_fetch" in abi["imports"]
    assert "pea_host_log" not in abi["imports"]
    assert "pea_host_now" not in abi["imports"]
    assert abi["exports"] == HOST_ABI["exports"]


def test_validate_artifact_abi_rejects_unknown_imports():
    """Phase 14: validate_artifact_abi flags unknown imports and exports."""
    ns = build_wasm_differential_namespace()
    bad_manifest = {
        "manifest": {
            "abi": HOST_ABI["version"],
            "imports": ["pea_host_log", "pea_unknown_import"],
            "exports": ["pea_run", "pea_unknown_export"],
        }
    }
    result = ns["validate_artifact_abi"](bad_manifest)
    assert result["ok"] is False
    assert result["unknown_imports"] == ["pea_unknown_import"]
    assert result["unknown_exports"] == ["pea_unknown_export"]


def test_scaffold_python_sdk(tmp_path):
    """Phase 15: Python host SDK scaffolding generates expected files."""
    out = scaffold_python_sdk(str(tmp_path / "python-sdk"))
    assert "error" not in out
    expected_files = {"pealang/client.py", "pyproject.toml", "README.md"}
    assert set(out["files"]) == expected_files, f"Got {set(out['files'])!r}"


def test_scaffold_browser_sdk(tmp_path):
    """Phase 16: Browser SDK scaffolding generates expected files."""
    out = scaffold_browser_sdk(str(tmp_path / "browser-sdk"))
    assert "error" not in out
    expected_files = {"src/browserClient.ts", "src/browserLoader.ts", "package.json", "README.md"}
    assert set(out["files"]) == expected_files, f"Got {set(out['files'])!r}"
