import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = str(Path(__file__).resolve().parent.parent)
ENV = {**os.environ, "PYTHONPATH": ROOT}


def test_cli_openapi_alias():
    with tempfile.NamedTemporaryFile('w', suffix='.pea', delete=False, encoding='utf-8') as f:
        f.write('let app = web.app()\napp.get("/x", function(req){ return web.text("x") })\n')
        name = f.name
    try:
        r = subprocess.run([sys.executable, '-m', 'pealang.cli', 'openapi', name],
                           capture_output=True, text=True, cwd=ROOT, env=ENV)
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert '/x' in data['paths']
    finally:
        os.unlink(name)


def test_cli_quickstart():
    r = subprocess.run([sys.executable, '-m', 'pealang.cli', 'quickstart'],
                       capture_output=True, text=True, cwd=ROOT, env=ENV)
    assert r.returncode == 0
    assert 'quickstart' in r.stdout.lower()
    assert 'pea' in r.stdout
