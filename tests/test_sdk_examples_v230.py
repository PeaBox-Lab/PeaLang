"""Phase 24: SDK example applications validation.

Verifies that example applications exist for all supported host SDKs
and that the example directory structure is complete.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_SDK_FILES = {
    "node": ["example.ts"],
    "go": ["example.go"],
    "python": ["example.py"],
    "browser": ["example.ts"],
    "java": ["Example.java"],
    "csharp": ["Example.cs"],
    "rust": ["example.rs"],
    "ruby": ["example.rb"],
    "php": ["example.php"],
}


def test_example_directory_exists():
    """examples/sdks/ directory exists with README."""
    sdk_dir = ROOT / "examples" / "sdks"
    assert sdk_dir.is_dir(), f"examples/sdks/ not found at {sdk_dir}"
    readme = sdk_dir / "README.md"
    assert readme.is_file(), f"examples/sdks/README.md not found"


def test_math_utils_pea_exists():
    """Example .pea source file exists for SDK codegen."""
    pea_file = ROOT / "examples" / "sdks" / "math_utils.pea"
    assert pea_file.is_file(), f"math_utils.pea not found at {pea_file}"
    content = pea_file.read_text(encoding="utf-8")
    assert "function add" in content
    assert "function multiply" in content
    assert "function greet" in content


def test_all_example_files_exist():
    """Every supported SDK has an example application file."""
    sdk_dir = ROOT / "examples" / "sdks"
    for lang, files in EXAMPLE_SDK_FILES.items():
        lang_dir = sdk_dir / lang
        assert lang_dir.is_dir(), f"examples/sdks/{lang}/ not found"
        for fname in files:
            example_file = lang_dir / fname
            assert example_file.is_file(), f"examples/sdks/{lang}/{fname} not found"
            content = example_file.read_text(encoding="utf-8")
            assert len(content) > 0, f"examples/sdks/{lang}/{fname} is empty"


def test_example_reads_math_utils():
    """Each example references the math_utils module."""
    sdk_dir = ROOT / "examples" / "sdks"
    for lang in EXAMPLE_SDK_FILES:
        lang_dir = sdk_dir / lang
        for f in lang_dir.iterdir():
            if f.suffix in (".ts", ".go", ".py", ".java", ".cs", ".rs", ".rb", ".php"):
                content = f.read_text(encoding="utf-8")
                assert "math_utils" in content, f"{f} does not reference math_utils"
