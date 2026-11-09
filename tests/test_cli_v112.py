import os
import subprocess
import sys

ROOT = r"C:\Users\Rajesh\Documents\My Apps\GitHub\PeaLang"
ENV = {**os.environ, "PYTHONPATH": ROOT}


def test_cli_env_name():
    env = {**ENV, "PEALANG_TEST_ENV": "hello123"}
    r = subprocess.run([sys.executable, '-m', 'pealang.cli', 'env', 'PEALANG_TEST_ENV'],
                       capture_output=True, text=True, cwd=ROOT, env=env)
    assert r.returncode == 0
    assert r.stdout.strip() == 'hello123'


def test_cli_env_keys():
    r = subprocess.run([sys.executable, '-m', 'pealang.cli', 'env', '--keys'],
                       capture_output=True, text=True, cwd=ROOT, env=ENV)
    assert r.returncode == 0
    assert 'PATH' in r.stdout or 'Path' in r.stdout or 'path' in r.stdout.lower()
