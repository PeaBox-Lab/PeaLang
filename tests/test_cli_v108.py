import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path

ROOT = str(Path(__file__).resolve().parent.parent)


def test_cli_check_json():
    with tempfile.NamedTemporaryFile('w', suffix='.pea', delete=False, encoding='utf-8') as f:
        f.write('print 1\n')
        name = f.name
    try:
        r = subprocess.run([sys.executable, '-m', 'pealang.cli', 'check', '--json', name],
                           capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data['ok'] is True
        assert data['errors'] == 0
    finally:
        os.unlink(name)


def test_cli_analyze_json():
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
        f.write('[{"a":1,"b":2},{"a":3,"b":4}]')
        name = f.name
    try:
        r = subprocess.run([sys.executable, '-m', 'pealang.cli', 'analyze', '--json', name],
                           capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data['rows'] == 2
        assert data['columns'] == 2
    finally:
        os.unlink(name)
