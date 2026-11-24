import subprocess, sys, os, tempfile
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_lock_create_and_check():
    """Phase 43: pea lock --check validates lock file against pea.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Initialize a library project (uses pea.toml)
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testlock'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testlock')
        assert os.path.exists(os.path.join(project_dir, 'pea.toml'))

        # Write pea.toml with dependencies
        pea_toml = os.path.join(project_dir, 'pea.toml')
        with open(pea_toml, 'w') as f:
            f.write('[project]\nname = "testlock"\nversion = "0.1.0"\nentry = "src/testlock.pea"\n')
            f.write('[dependencies]\n')
            f.write('"mylib" = { path = "./mylib" }\n')
            f.write('"otherlib" = { registry = "http://127.0.0.1:8788" }\n')

        # Create lock file
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'lock', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        # Check lock consistency (should pass)
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'lock', '--check', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0
        out = json.loads(result.stdout)
        assert out['ok'] is True

        # Modify pea.toml to break consistency
        with open(pea_toml, 'a') as f:
            f.write('"newlib" = { path = "./newlib" }\n')

        # Check lock consistency (should fail)
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'lock', '--check', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 1
        out = json.loads(result.stdout)
        assert out['ok'] is False
        assert any('newlib' in issue for issue in out['issues'])

def test_pea_deps_list():
    """Phase 43: pea deps lists dependencies with lock info."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Initialize a library project (uses pea.toml)
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testdeps'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testdeps')

        # Write pea.toml with dependencies
        pea_toml = os.path.join(project_dir, 'pea.toml')
        with open(pea_toml, 'w') as f:
            f.write('[project]\nname = "testdeps"\nversion = "0.1.0"\nentry = "src/testdeps.pea"\n')
            f.write('[dependencies]\n')
            f.write('"mylib" = { path = "./mylib" }\n')
            f.write('"otherlib" = { registry = "http://127.0.0.1:8788" }\n')

        # Create lock file
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'lock', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        # List dependencies
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'deps', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        deps = data['dependencies']
        assert len(deps) == 2
        assert deps[0]['name'] == 'mylib'
        assert deps[1]['name'] == 'otherlib'
        assert deps[0]['source'] == 'path'
        assert deps[1]['source'] == 'registry'
        for dep in deps:
            assert 'lock' in dep