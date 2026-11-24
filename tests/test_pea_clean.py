import subprocess, sys, os, tempfile
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_clean_basic():
    """Phase 48: pea clean removes .pea_modules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Init a library project
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testclean'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testclean')

        # Seed .pea_modules with fake content
        pea_modules = os.path.join(project_dir, '.pea_modules', 'somelib')
        os.makedirs(pea_modules, exist_ok=True)
        with open(os.path.join(pea_modules, 'main.pea'), 'w') as f:
            f.write('function foo() { return 1 }\n')

        # Run clean
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'clean', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        data = json.loads(result.stdout)
        assert data['ok'] == True
        assert '.pea_modules' in data['removed']
        assert not os.path.exists(pea_modules)

def test_pea_clean_with_all():
    """Phase 48: pea clean --all also removes pea.lock."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Init a library project
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testclean2'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testclean2')

        # Create lock file
        lock_path = os.path.join(project_dir, 'pea.lock')
        with open(lock_path, 'w') as f:
            json.dump({'lock_version': 1}, f)

        # Seed .pea_modules
        pea_modules = os.path.join(project_dir, '.pea_modules', 'somelib')
        os.makedirs(pea_modules, exist_ok=True)
        with open(os.path.join(pea_modules, 'main.pea'), 'w') as f:
            f.write('function foo() { return 1 }\n')

        # Run clean --all
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'clean', project_dir, '--all'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        data = json.loads(result.stdout)
        assert data['ok'] == True
        assert '.pea_modules' in data['removed']
        assert 'pea.lock' in data['removed']
        assert not os.path.exists(pea_modules)
        assert not os.path.exists(lock_path)

if __name__ == '__main__':
    test_pea_clean_basic()
    test_pea_clean_with_all()
    print("All clean tests passed!")