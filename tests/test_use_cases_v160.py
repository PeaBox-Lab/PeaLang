"""Regression coverage for v1.6.0 Arrow backend use case."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_use_case_40_arrow_backend():
    script = REPO_ROOT / "examples" / "use_cases" / "40_arrow_backend.pea"
    result = subprocess.run(
        [sys.executable, "-m", "pealang", "run", str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
