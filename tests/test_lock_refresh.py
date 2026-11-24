import json
import os
import subprocess
import sys

from pealang.package_manager import init_manifest, lock_drift, refresh_lock, write_lock

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _write_manifest(root, extra_deps=''):
    manifest = root / 'pea.toml'
    manifest.write_text(
        '[project]\n'
        'name = "app"\n'
        'version = "0.1.0"\n'
        'entry = "src/main.pea"\n'
        '\n'
        '[dependencies]\n'
        + extra_deps
        + '\n'
        '[permissions]\n'
        'allow = []\n',
        encoding='utf-8',
    )


def _project(tmp_path):
    app = tmp_path / 'app'
    init_manifest(app, 'app')
    dep = app / 'dep'
    init_manifest(dep, 'dep')
    _write_manifest(app, 'dep = { path = "dep" }\n')
    return app, dep


def test_lock_drift_detects_manifest_checksum_change(tmp_path):
    """Phase 52: changing a path dependency manifest is reported as drift."""
    app, dep = _project(tmp_path)
    write_lock(app)

    clean = lock_drift(app)
    assert clean['ok'] is True
    assert clean['changes'] == []

    manifest = dep / 'pea.toml'
    manifest.write_text(manifest.read_text(encoding='utf-8') + '\n# changed\n', encoding='utf-8')
    drift = lock_drift(app)
    assert drift['ok'] is False
    assert any(change['field'] == 'dep.manifest_sha256' for change in drift['changes'])

    report = refresh_lock(app)
    assert report['ok'] is True
    assert lock_drift(app)['ok'] is True


def test_lock_drift_detects_added_dependency(tmp_path):
    """Phase 52: manifest dependency additions and removals are reported."""
    app, _ = _project(tmp_path)
    write_lock(app)

    _write_manifest(app, 'dep = { path = "dep" }\nextra = { registry = "http://127.0.0.1:8788" }\n')
    drift = lock_drift(app)
    assert drift['ok'] is False
    assert any("Dependency 'extra' in pea.toml but not in lock" in issue for issue in drift['issues'])

    refresh_lock(app)
    assert lock_drift(app)['ok'] is True


def test_lock_write_is_deterministic(tmp_path):
    """Phase 52: identical inputs produce byte-identical lockfiles."""
    app, _ = _project(tmp_path)
    first, first_lock = write_lock(app)
    first_bytes = first.read_bytes()
    second, second_lock = write_lock(app)
    assert first_bytes == second.read_bytes()
    assert first_lock == second_lock


def test_pea_lock_update_cli(tmp_path):
    """Phase 52: pea lock --update writes a machine-readable refresh report."""
    app, _ = _project(tmp_path)
    env = dict(os.environ)
    env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'lock', '--update', str(app)],
        capture_output=True, text=True, cwd=tmp_path, env=env,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['ok'] is True
    assert report['updated'] is True
    assert len(report['sha256']) == 64

    check = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'lock', '--check', str(app)],
        capture_output=True, text=True, cwd=tmp_path, env=env,
    )
    assert check.returncode == 0, check.stderr
    assert json.loads(check.stdout)['ok'] is True
