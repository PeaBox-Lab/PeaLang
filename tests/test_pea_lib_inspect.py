import json
import os
import subprocess
import sys

from pealang.package_manager import build_library, init_manifest, inspect_library

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _make_library(tmp_path, name='mylib'):
    root = tmp_path / name
    init_manifest(root, name)
    manifest = root / 'pea.toml'
    manifest.write_text(
        manifest.read_text(encoding='utf-8')
        + '\n[library]\nexports = ["greet"]\n',
        encoding='utf-8',
    )
    return root


def test_inspect_library_function(tmp_path):
    """Phase 50: inspect_library reads .pelib metadata without installing."""
    root = _make_library(tmp_path)
    package, _ = build_library(root)
    info = inspect_library(package)
    assert info['ok'] is True
    assert info['name'] == 'mylib'
    assert info['version'] == '0.1.0'
    assert info['format'] == 'pelib'
    assert info['exports'] == ['greet']
    assert 'manifest.json' in info['files']
    assert len(info['sha256']) == 64


def test_pea_lib_inspect_cli(tmp_path):
    """Phase 50: pea lib inspect prints human and JSON output."""
    root = _make_library(tmp_path, 'clilib')
    package, _ = build_library(root)
    env = dict(os.environ)
    env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'lib', 'inspect', str(package)],
        capture_output=True, text=True, cwd=tmp_path, env=env,
    )
    assert result.returncode == 0, result.stderr
    assert 'Package: clilib 0.1.0' in result.stdout
    assert 'Exports: greet' in result.stdout

    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'lib', 'inspect', str(package), '--json'],
        capture_output=True, text=True, cwd=tmp_path, env=env,
    )
    assert result.returncode == 0, result.stderr
    info = json.loads(result.stdout)
    assert info['name'] == 'clilib'
    assert info['exports'] == ['greet']
