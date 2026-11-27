"""Phase 18: Unified host SDK compatibility validation.

Verifies that every scaffold_*_sdk function produces the expected file set,
and that the CLI `pea sdk` command can list and generate each SDK.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.host_bindings import (
    build_host_sdk_namespace,
    HOST_SDK_NAMES,
    scaffold_node_sdk,
    scaffold_go_sdk,
    scaffold_python_sdk,
    scaffold_browser_sdk,
    scaffold_java_sdk,
    scaffold_csharp_sdk,
    scaffold_rust_sdk,
    scaffold_ruby_sdk,
    scaffold_php_sdk,
    scaffold_library,
    generate_sdk_from_source,
)

EXPECTED_SDK_FILES = {
    "node": {"src/index.ts", "package.json", "tsconfig.json", "README.md"},
    "go": {"pealang/client.go", "go.mod", "README.md"},
    "python": {"pealang/client.py", "pyproject.toml", "README.md"},
    "browser": {"src/browserClient.ts", "src/browserLoader.ts", "package.json", "README.md"},
    "java": {
        "src/main/java/io/pealang/client/SdkClient.java",
        "pom.xml",
        "src/main/resources/application.yml",
        "README.md",
    },
    "csharp": {
        "pealang/SdkClient.cs",
        "pealang.csproj",
        "appsettings.json",
        "README.md",
    },
    "rust": {
        "src/main.rs",
        "Cargo.toml",
        "README.md",
    },
    "ruby": {
        "lib/pealang/client.rb",
        "Gemfile",
        "README.md",
    },
    "php": {
        "src/PeaClient.php",
        "composer.json",
        "README.md",
    },
    "library": {
        "pea.toml",
        "src/mylib.pea",
        "tests/test_mylib.pea",
        "README.md",
        "LICENSE",
    },
}

SCAF_FN = {
    "node": scaffold_node_sdk,
    "go": scaffold_go_sdk,
    "python": scaffold_python_sdk,
    "browser": scaffold_browser_sdk,
    "java": scaffold_java_sdk,
    "csharp": scaffold_csharp_sdk,
    "rust": scaffold_rust_sdk,
    "ruby": scaffold_ruby_sdk,
    "php": scaffold_php_sdk,
}


def _run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "pealang.cli", *args],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )


def test_all_sdks_in_namespace():
    """build_host_sdk_namespace exposes all scaffold functions plus codegen."""
    ns = build_host_sdk_namespace()
    assert set(ns.keys()) == {
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


def test_all_sdks_in_cli_map():
    """HOST_SDK_NAMES maps each supported language to its scaffold function."""
    assert set(HOST_SDK_NAMES.keys()) == {
        "node", "go", "python", "browser", "java", "csharp", "rust", "ruby", "php", "library",
    }
    for lang, fn in HOST_SDK_NAMES.items():
        out = fn(f"/tmp/pea-sdk-{lang}-test")
        assert "root" in out
        assert "files" in out


def test_each_sdk_produces_expected_files(tmp_path):
    """Every scaffold_*_sdk emits its expected file set."""
    cases = [
        ("node", scaffold_node_sdk, EXPECTED_SDK_FILES["node"]),
        ("go", scaffold_go_sdk, EXPECTED_SDK_FILES["go"]),
        ("python", scaffold_python_sdk, EXPECTED_SDK_FILES["python"]),
        ("browser", scaffold_browser_sdk, EXPECTED_SDK_FILES["browser"]),
        ("java", scaffold_java_sdk, EXPECTED_SDK_FILES["java"]),
        ("csharp", scaffold_csharp_sdk, EXPECTED_SDK_FILES["csharp"]),
        ("rust", scaffold_rust_sdk, EXPECTED_SDK_FILES["rust"]),
        ("ruby", scaffold_ruby_sdk, EXPECTED_SDK_FILES["ruby"]),
        ("php", scaffold_php_sdk, EXPECTED_SDK_FILES["php"]),
        ("library", scaffold_library, EXPECTED_SDK_FILES["library"]),
    ]
    for lang, fn, expected in cases:
        out = fn(str(tmp_path / f"{lang}-sdk"))
        assert "error" not in out, f"{lang}: {out}"
        assert set(out["files"]) == expected, f"{lang}: got {set(out['files'])!r}, expected {expected!r}"


def test_pea_sdk_list():
    """pea sdk list reports all available SDK languages."""
    result = _run_cli("sdk", "list")
    assert result.returncode == 0, result.stderr
    for lang in ("node", "go", "python", "browser", "java", "csharp", "rust", "ruby", "php", "library"):
        assert lang in result.stdout


def test_pea_sdk_generate_each_lang(tmp_path):
    """pea sdk generate <lang> <dir> creates files for every supported language."""
    for lang in ("node", "go", "python", "browser", "java", "csharp", "rust", "ruby", "php", "library"):
        target = str(tmp_path / f"{lang}-sdk")
        result = _run_cli("sdk", "generate", lang, target)
        assert result.returncode == 0, f"{lang}: {result.stderr}"
        for rel in EXPECTED_SDK_FILES[lang]:
            assert Path(target, rel).exists(), f"{lang}: missing {rel}"


def test_pea_sdk_generate_unknown_lang():
    """pea sdk generate with an unknown language returns nonzero."""
    result = _run_cli("sdk", "generate", "cobol", "/tmp/pea-cobol")
    assert result.returncode == 1
    assert "Unknown SDK language" in result.stdout or "Unknown SDK language" in result.stderr


def test_generate_sdk_from_source_each_lang(tmp_path):
    """generate_sdk_from_source produces typed clients for every language."""
    source = "function add(a, b) {\n  return a + b\n}\nfunction greet(name) {\n  print \"Hello \" + name\n}"
    for lang in ("node", "go", "python", "browser", "java", "csharp", "rust", "ruby", "php"):
        target = str(tmp_path / f"codegen-{lang}")
        out = generate_sdk_from_source(source, lang, target)
        assert "error" not in out, f"{lang}: {out}"
        assert len(out["files"]) > 0, f"{lang}: no files generated"
        for rel in out["files"]:
            assert Path(target, rel).exists(), f"{lang}: missing {rel}"


def test_generate_sdk_from_source_contains_function_names(tmp_path):
    """Generated client code references functions declared in the .pea source."""
    source = "function add(a, b) {\n  return a + b\n}\nfunction multiply(x, y) {\n  return x * y\n}"
    target = str(tmp_path / "codegen-node")
    out = generate_sdk_from_source(source, "node", target)
    client = Path(target, "src/client.ts").read_text(encoding="utf-8")
    assert "add" in client
    assert "multiply" in client
    assert "health" in client


def test_pea_sdk_codegen_cli(tmp_path):
    """pea sdk-codegen <source> <lang> <dir> works via CLI."""
    source_file = tmp_path / "test.pea"
    source_file.write_text("function add(a, b) {\n  return a + b\n}", encoding="utf-8")
    target = str(tmp_path / "codegen-cli")
    result = _run_cli("sdk-codegen", str(source_file), "python", target)
    assert result.returncode == 0, result.stderr
    assert Path(target, "pealang/client.py").exists()
    assert Path(target, "pyproject.toml").exists()
