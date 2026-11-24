import json
import os
import subprocess
import sys

from pealang.package_manager import dependency_graph

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _write_project(path, name, version, deps=None):
    path.mkdir(parents=True, exist_ok=True)
    (path / 'main.pea').write_text('print "ok"\n', encoding='utf-8')
    lines = [
        '[project]',
        f'name = "{name}"',
        f'version = "{version}"',
        'entry = "main.pea"',
        '',
        '[dependencies]',
    ]
    for dep_name, dep_path in (deps or {}).items():
        lines.append(f'"{dep_name}" = {{ path = "{dep_path}" }}')
    (path / 'pea.toml').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def test_dependency_graph_detects_cycle(tmp_path):
    """Phase 51: cycle detection marks the repeated path dependency."""
    _write_project(tmp_path / 'app', 'app', '0.1.0', {'a': '../libA'})
    _write_project(tmp_path / 'libA', 'a', '1.0.0', {'b': '../libB'})
    _write_project(tmp_path / 'libB', 'b', '1.0.0', {'a': '../libA'})

    report = dependency_graph(tmp_path / 'app')
    assert report['ok'] is False
    assert len(report['cycles']) == 1
    assert report['cycles'][0]['cycle'] == ['a', 'b', 'a']
    cycle_node = report['tree'][0]['children'][0]['children'][0]
    assert cycle_node['name'] == 'a'
    assert cycle_node['cycle'] is True


def test_dependency_graph_detects_version_conflict(tmp_path):
    """Phase 51: the same dependency name at different versions is a conflict."""
    _write_project(tmp_path / 'app', 'app', '0.1.0', {'a': '../libA1', 'b': '../libB'})
    _write_project(tmp_path / 'libA1', 'a', '1.0.0')
    _write_project(tmp_path / 'libA2', 'a', '2.0.0')
    _write_project(tmp_path / 'libB', 'b', '1.0.0', {'a': '../libA2'})

    report = dependency_graph(tmp_path / 'app')
    assert report['ok'] is False
    assert report['cycles'] == []
    conflict = next(c for c in report['conflicts'] if c['name'] == 'a')
    assert conflict['versions'] == ['1.0.0', '2.0.0']


def test_pea_deps_tree_json_reports_cycle(tmp_path):
    """Phase 51: pea deps --tree --json exits non-zero when issues exist."""
    _write_project(tmp_path / 'app', 'app', '0.1.0', {'a': '../libA'})
    _write_project(tmp_path / 'libA', 'a', '1.0.0', {'b': '../libB'})
    _write_project(tmp_path / 'libB', 'b', '1.0.0', {'a': '../libA'})

    env = dict(os.environ)
    env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')
    result = subprocess.run(
        [sys.executable, '-m', 'pealang.cli', 'deps', '--tree', '--json', str(tmp_path / 'app')],
        capture_output=True, text=True, cwd=tmp_path, env=env,
    )
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report['ok'] is False
    assert report['cycles'][0]['cycle'] == ['a', 'b', 'a']
