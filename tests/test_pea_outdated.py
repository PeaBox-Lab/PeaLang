import subprocess, sys, os, tempfile
import json
import shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_outdated_ok():
    """Phase 46: pea outdated reports ok when all deps match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Init a library project
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testoutd'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testoutd')

        # Create source library with pea.toml
        lib_src = os.path.join(tmpdir, 'mylib')
        os.makedirs(lib_src, exist_ok=True)
        with open(os.path.join(lib_src, 'main.pea'), 'w') as f:
            f.write('function add(a, b) { return a + b }\n')
        with open(os.path.join(lib_src, 'pea.toml'), 'w') as f:
            f.write('[project]\nname = "mylib"\nversion = "0.2.0"\nentry = "main.pea"\n')

        # Write pea.toml with path dependency
        pea_toml = os.path.join(project_dir, 'pea.toml')
        with open(pea_toml, 'w') as f:
            f.write('[project]\nname = "testoutd"\nversion = "0.1.0"\nentry = "src/testoutd.pea"\n')
            f.write('[dependencies]\n')
            f.write('"mylib" = { path = "../mylib" }\n')

        # Generate lock
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'lock', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        # Create .pea_modules manually (copy from source)
        pea_modules = os.path.join(project_dir, '.pea_modules')
        os.makedirs(pea_modules, exist_ok=True)
        shutil.copytree(lib_src, os.path.join(pea_modules, 'mylib'))

        # Run outdated
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'outdated', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr
        out = json.loads(result.stdout)
        assert out['ok'] is True
        assert out['outdated_count'] == 0
        for dep in out['dependencies']:
            assert dep['status'] == 'ok'

def test_pea_outdated_missing():
    """Phase 46: pea outdated reports missing if not installed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Init a library project
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testoutd2'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testoutd2')

        # Create source library with pea.toml
        lib_src = os.path.join(tmpdir, 'mylib')
        os.makedirs(lib_src, exist_ok=True)
        with open(os.path.join(lib_src, 'main.pea'), 'w') as f:
            f.write('function add(a, b) { return a + b }\n')
        with open(os.path.join(lib_src, 'pea.toml'), 'w') as f:
            f.write('[project]\nname = "mylib"\nversion = "0.2.0"\nentry = "main.pea"\n')

        # Write pea.toml with path dependency
        pea_toml = os.path.join(project_dir, 'pea.toml')
        with open(pea_toml, 'w') as f:
            f.write('[project]\nname = "testoutd2"\nversion = "0.1.0"\nentry = "src/testoutd2.pea"\n')
            f.write('[dependencies]\n')
            f.write('"mylib" = { path = "../mylib" }\n')

        # Generate lock
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'lock', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        # Do NOT install

        # Run outdated
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'outdated', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 1, result.stderr
        out = json.loads(result.stdout)
        assert out['ok'] is False
        assert out['outdated_count'] == 1
        assert out['dependencies'][0]['status'] == 'missing'

if __name__ == '__main__':
    test_pea_outdated_ok()
    test_pea_outdated_missing()
    print("All outdated tests passed!")