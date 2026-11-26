"""Phase 23: 0.40/0.41 Conformance & Quality Gate validation.

Validates that CI prerequisites for the conformance and performance gates are
met: conformance report passes, version surfaces agree, all host SDKs
scaffold correctly, and CLI commands produce valid output.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang import __version__
from pealang.conformance import conformance_report
from pealang.host_bindings import build_host_sdk_namespace, HOST_SDK_NAMES


def test_conformance_report_passes():
    """0.40: conformance_report must pass (conformance + fuzz)."""
    report = conformance_report()
    assert report["conformance"]["ok"] is True
    assert report["fuzz"]["ok"] is True


def test_pea_conformance_cli():
    """0.40: `pea conformance` CLI exits 0 with valid JSON report."""
    result = subprocess.run(
        [sys.executable, "-m", "pealang.cli", "conformance"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["conformance"]["ok"] is True


def test_version_surface_consistent():
    """0.40: pealang.__version__ matches the expected release version."""
    # Version is pinned at the current tagged release line.
    assert __version__ == "5.10.0"


def test_all_host_sdks_scaffold():
    """0.41: all ten host SDKs scaffold without error."""
    for lang, fn in HOST_SDK_NAMES.items():
        out = fn(f"/tmp/pea-quality-{lang}")
        assert "error" not in out, f"{lang}: {out}"
        assert "root" in out
        assert "files" in out


def test_build_host_sdk_namespace_complete():
    """0.41: unified SDK namespace exposes all scaffold + codegen functions."""
    ns = build_host_sdk_namespace()
    expected = {
        "scaffold_node_sdk",
        "scaffold_go_sdk",
        "scaffold_python_sdk",
        "scaffold_browser_sdk",
        "scaffold_java_sdk",
        "scaffold_csharp_sdk",
        "scaffold_rust_sdk",
        "scaffold_ruby_sdk",
        "scaffold_php_sdk",
        "scaffold_library",
        "generate_sdk_from_source",
    }
    assert set(ns.keys()) == expected


def test_pea_sdk_cli_list():
    """0.41: `pea sdk list` exits 0 and lists all SDKs."""
    result = subprocess.run(
        [sys.executable, "-m", "pealang.cli", "sdk", "list"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert result.returncode == 0, result.stderr
    for lang in ("node", "go", "python", "browser", "java", "csharp", "rust", "ruby", "php", "library"):
        assert lang in result.stdout


def test_pea_sdk_cli_generate(tmp_path):
    """0.41: `pea sdk generate <lang> <dir>` creates files for every language."""
    for lang in ("node", "go", "python", "browser", "java", "csharp", "rust", "ruby", "php", "library"):
        target = str(tmp_path / f"quality-{lang}")
        result = subprocess.run(
            [sys.executable, "-m", "pealang.cli", "sdk", "generate", lang, target],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        assert result.returncode == 0, f"{lang}: {result.stderr}"
        assert Path(target).is_dir()


def test_pea_registry_cli_help(tmp_path):
    """0.41: `pea registry serve` CLI command exists and is invocable."""
    result = subprocess.run(
        [sys.executable, "-m", "pealang.cli", "registry"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    # Should show usage, not crash
    assert result.returncode == 1, "Expected usage error for missing subcommand"
    assert "Usage" in result.stdout or "Usage" in result.stderr


def test_pea_publish_cli_help(tmp_path):
    """0.41: `pea publish` CLI command shows usage."""
    result = subprocess.run(
        [sys.executable, "-m", "pealang.cli", "publish"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert result.returncode == 1
    assert "Usage: pea publish" in result.stdout


def test_pea_search_cli_help(tmp_path):
    """0.41: `pea search` CLI command shows usage."""
    result = subprocess.run(
        [sys.executable, "-m", "pealang.cli", "search"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert result.returncode == 1
    assert "Usage: pea search" in result.stdout


def test_pea_login_cli_help(tmp_path):
    """0.41: `pea login` CLI command shows usage."""
    result = subprocess.run(
        [sys.executable, "-m", "pealang.cli", "login"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert result.returncode == 1
    assert "Usage: pea login" in result.stdout


def test_pea_benchmark_plain_output(tmp_path):
    """0.41: `pea benchmark` plain output produces valid JSON."""
    src = tmp_path / "bench.pea"
    src.write_text("let x = 2\nprint x + 3", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "pealang.cli", "benchmark", str(src), "--iterations", "5"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["iterations"] == 5
    assert data["median_ms"] >= 0
