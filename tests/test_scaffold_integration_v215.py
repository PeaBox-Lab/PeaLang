"""End-to-end scaffold integration (2.15.0 planned item).

Generates a FastAPI service with ``frameworks.write_scaffold``, runs the
generated test suite, then boots the app with uvicorn and probes ``/health``.
Skipped when FastAPI/uvicorn are not installed; CI installs them from the
generated ``requirements.txt``.
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

from pealang.frameworks import write_scaffold

pytest.importorskip("fastapi")
pytest.importorskip("uvicorn")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_generated_fastapi_service_tests_and_serves(tmp_path):
    target = Path(tmp_path) / "svc"
    write_port = _free_port()
    out = write_scaffold(
        "svc", kind="backend", target_dir=str(target),
        framework="fastapi", port=write_port,
    )
    assert "error" not in out
    assert (target / "app" / "main.py").exists()

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests"],
        cwd=str(target), capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    serve_port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(serve_port), "--log-level", "warning"],
        cwd=str(target), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        payload = None
        for _ in range(80):
            time.sleep(0.25)
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{serve_port}/health", timeout=2
                ) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    break
            except Exception:
                continue
        assert payload == {"status": "ok", "service": "svc"}, payload
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
