"""Regression coverage for v1.8.0 notebook IDE use case."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_use_case_42_notebook_ide():
    script = REPO_ROOT / "examples" / "use_cases" / "42_notebook_ide.pea"
    result = subprocess.run(
        [sys.executable, "-m", "pealang", "run", str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
