import subprocess, sys, os, tempfile
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_uninstall_removes_installed():
    """Phase 44: pea uninstall removes installed library from .pea_modules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Initialize a library project (uses pea.toml)
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testuninst'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testuninst')
        assert os.path.exists(os.path.join(project_dir, 'pea.toml'))

        # Manually create .pea_modules and install mylib
        pea_modules = os.path.join(project_dir, '.pea_modules', 'mylib')
        os.makedirs(pea_modules, exist_ok=True)
        with open(os.path.join(pea_modules, 'main.pea'), 'w') as f:
            f.write('function add(a, b) {\n    return a + b\n}\nexport add\n')

        # Uninstall it
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'uninstall', 'mylib', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr
        out = json.loads(result.stdout)
        assert out['removed'] is True
        assert not os.path.exists(pea_modules)

def test_pea_uninstall_not_installed():
    """Phase 44: pea uninstall errors cleanly when library not installed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Initialize a library project (uses pea.toml)
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testuninst2'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testuninst2')

        # Uninstall nonexistent library
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'uninstall', 'nonexistent', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 1
        assert 'not installed' in result.stderr