"""Regression coverage for v1.5.0 web SDK use case."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_use_case_39_web_sdk():
    script = REPO_ROOT / "examples" / "use_cases" / "39_web_sdk.pea"
    result = subprocess.run(
        [sys.executable, "-m", "pealang", "run", str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
