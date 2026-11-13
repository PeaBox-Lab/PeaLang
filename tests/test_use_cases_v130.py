"""Regression coverage for v130 document processing use case."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_use_case_26_documents():
    script = REPO_ROOT / "examples" / "use_cases" / "26_documents.pea"
    result = subprocess.run(
        [sys.executable, "-m", "pealang", "run", str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
