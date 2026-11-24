import subprocess, sys, os, tempfile
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_update_all():
    """Phase 45: pea update refreshes all installed libraries from pea.lock."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Init a library project
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testupdate'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testupdate')

        # Create source library
        lib_src = os.path.join(tmpdir, 'mylib')
        os.makedirs(lib_src, exist_ok=True)
        with open(os.path.join(lib_src, 'main.pea'), 'w') as f:
            f.write('function new_func(a, b) { return a + b }\n')

        # Write pea.toml with path dependency
        pea_toml = os.path.join(project_dir, 'pea.toml')
        with open(pea_toml, 'w') as f:
            f.write('[project]\nname = "testupdate"\nversion = "0.1.0"\nentry = "src/testupdate.pea"\n')
            f.write('[dependencies]\n')
            f.write('"mylib" = { path = "../mylib" }\n')

        # Generate lock file manually (same shape as write_lock output)
        lock_path = os.path.join(project_dir, 'pea.lock')
        lock_content = {
            'lock_version': 1,
            'pealang': '0.35.0',
            'package': {'name': 'testupdate', 'version': '0.1.0'},
            'dependencies': [
                {
                    'name': 'mylib',
                    'version': '0.2.0',
                    'source': 'path',
                    'path': '../mylib',
                    'manifest_sha256': 'sha256_of_mylib',
                    'permissions': []
                }
            ]
        }
        with open(lock_path, 'w') as f:
            json.dump(lock_content, f)

        # Seed old content in .pea_modules
        pea_modules = os.path.join(project_dir, '.pea_modules', 'mylib')
        os.makedirs(pea_modules, exist_ok=True)
        with open(os.path.join(pea_modules, 'main.pea'), 'w') as f:
            f.write('function old_func(a, b) { return a + b }\n')

        # Run update
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'update', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        # Verify updated content
        main_pea = os.path.join(pea_modules, 'main.pea')
        assert os.path.exists(main_pea)
        with open(main_pea, 'r') as f:
            assert 'new_func' in f.read()

def test_pea_update_specific():
    """Phase 45: pea update <name> updates specific library."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Init a library project
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testupd2'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testupd2')

        # Create source library
        lib_src = os.path.join(tmpdir, 'mylib')
        os.makedirs(lib_src, exist_ok=True)
        with open(os.path.join(lib_src, 'main.pea'), 'w') as f:
            f.write('function new_func(a, b) { return a + b }\n')

        # Write pea.toml with path dependency
        pea_toml = os.path.join(project_dir, 'pea.toml')
        with open(pea_toml, 'w') as f:
            f.write('[project]\nname = "testupd2"\nversion = "0.1.0"\nentry = "src/testupd2.pea"\n')
            f.write('[dependencies]\n')
            f.write('"mylib" = { path = "../mylib" }\n')

        # Generate lock file manually
        lock_path = os.path.join(project_dir, 'pea.lock')
        lock_content = {
            'lock_version': 1,
            'pealang': '0.35.0',
            'package': {'name': 'testupd2', 'version': '0.1.0'},
            'dependencies': [
                {
                    'name': 'mylib',
                    'version': '0.2.0',
                    'source': 'path',
                    'path': '../mylib',
                    'manifest_sha256': 'sha256_of_mylib',
                    'permissions': []
                }
            ]
        }
        with open(lock_path, 'w') as f:
            json.dump(lock_content, f)

        # Seed old content
        pea_modules = os.path.join(project_dir, '.pea_modules', 'mylib')
        os.makedirs(pea_modules, exist_ok=True)
        with open(os.path.join(pea_modules, 'main.pea'), 'w') as f:
            f.write('function old_func(a, b) { return a + b }\n')

        # Run update specific
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'update', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        # Verify updated content
        main_pea = os.path.join(pea_modules, 'main.pea')
        assert os.path.exists(main_pea)
        with open(main_pea, 'r') as f:
            assert 'new_func' in f.read()

if __name__ == '__main__':
    test_pea_update_all()
    test_pea_update_specific()
    print("All update tests passed!")