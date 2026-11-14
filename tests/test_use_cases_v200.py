"""Regression coverage for v2.0.0 VM optimizer use case."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_use_case_44_vm_optimizer():
    script = REPO_ROOT / "examples" / "use_cases" / "44_vm_optimizer.pea"
    result = subprocess.run(
        [sys.executable, "-m", "pealang", "run", str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
