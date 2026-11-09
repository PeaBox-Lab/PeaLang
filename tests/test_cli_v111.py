import json
import os
import subprocess
import sys

ROOT = r"C:\Users\Rajesh\Documents\My Apps\GitHub\PeaLang"
ENV = {**os.environ, "PYTHONPATH": ROOT}


def test_cli_version_json():
    r = subprocess.run([sys.executable, '-m', 'pealang.cli', 'version', '--json'],
                       capture_output=True, text=True, cwd=ROOT, env=ENV)
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert "version" in data


def test_cli_tree():
    r = subprocess.run([sys.executable, '-m', 'pealang.cli', 'tree', 'tests'],
                       capture_output=True, text=True, cwd=ROOT, env=ENV)
    assert r.returncode == 0
    assert '.pea' in r.stdout or 'file(s)' in r.stdout
