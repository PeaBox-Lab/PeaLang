import json
import os
import subprocess
import sys
import tempfile

ROOT = r"C:\Users\Rajesh\Documents\My Apps\GitHub\PeaLang"
ENV = {**os.environ, "PYTHONPATH": ROOT}


def test_cli_hash():
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write('abc')
        name = f.name
    try:
        r = subprocess.run([sys.executable, '-m', 'pealang.cli', 'hash', name],
                           capture_output=True, text=True, cwd=ROOT, env=ENV)
        assert r.returncode == 0
        assert len(r.stdout.strip()) == 64
    finally:
        os.unlink(name)


def test_cli_web_openapi():
    with tempfile.NamedTemporaryFile('w', suffix='.pea', delete=False, encoding='utf-8') as f:
        f.write('let app = web.app()\napp.get("/hi", function(req){ return web.text("hi") })\n')
        name = f.name
    try:
        r = subprocess.run([sys.executable, '-m', 'pealang.cli', 'web-openapi', name, '--title', 'T', '--version', '2.0.0'],
                           capture_output=True, text=True, cwd=ROOT, env=ENV)
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert data['openapi'] == '3.0.3'
        assert data['info']['title'] == 'T'
        assert '/hi' in data['paths']
    finally:
        os.unlink(name)
