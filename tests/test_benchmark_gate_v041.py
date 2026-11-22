"""Performance baseline gate tests for `pea benchmark` (roadmap 0.41)."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(*args):
    return subprocess.run(
        [sys.executable, "-m", "pealang.cli", "benchmark", *args],
        capture_output=True, text=True, cwd=ROOT,
    )


def test_benchmark_plain_output(tmp_path):
    src = tmp_path / "bench.pea"
    src.write_text("let x = 2\nprint x + 3", encoding="utf-8")
    result = _run(str(src), "--iterations", "5")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["iterations"] == 5
    assert data["median_ms"] >= 0


def test_benchmark_save_and_compare(tmp_path):
    src = tmp_path / "bench.pea"
    src.write_text("let total = 0\nfor i in [1, 2, 3] {\n  total = total + i\n}\nprint total", encoding="utf-8")
    baseline = tmp_path / "baseline.json"

    saved = _run(str(src), "--save-baseline", str(baseline), "--iterations", "5")
    assert saved.returncode == 0, saved.stderr
    assert baseline.exists()
    payload = json.loads(baseline.read_text(encoding="utf-8"))
    assert "median_ms" in payload

    compared = _run(str(src), "--baseline", str(baseline), "--iterations", "5")
    assert compared.returncode == 0, compared.stdout + compared.stderr
    report = json.loads(compared.stdout)
    assert report["ok"] is True
    assert report["threshold_pct"] == 10.0


def test_benchmark_missing_source(tmp_path):
    result = _run(str(tmp_path / "missing.pea"))
    assert result.returncode == 1
    assert "not found" in result.stdout
