"""Regression coverage for v2.1.0 performance use case."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_use_case_45_performance():
    script = REPO_ROOT / "examples" / "use_cases" / "45_performance.pea"
    result = subprocess.run(
        [sys.executable, "-m", "pealang", "run", str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
