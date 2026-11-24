import subprocess, sys, os, tempfile
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_lib_runtime_resolve_module():
    """Phase 41: resolve_module finds libraries installed in .pea_modules."""
    from pealang.project import resolve_module
    import tempfile, os

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, 'myapp')
        pea_mod_dir = os.path.join(project_dir, '.pea_modules', 'mylib')
        os.makedirs(pea_mod_dir)

        # Create a simple library entry point
        main_pea = os.path.join(pea_mod_dir, 'main.pea')
        with open(main_pea, 'w') as f:
            f.write('print "Hello from mylib!"\n')

        # Also create pea.toml so resolve_module uses the manifest entry
        pea_toml = os.path.join(pea_mod_dir, 'pea.toml')
        with open(pea_toml, 'w') as f:
            f.write('[project]\nname = "mylib"\nversion = "0.1.0"\nentry = "main.pea"\n')

        result = resolve_module('mylib', project_dir, project_dir, {})
        assert result.exists()
        assert str(result).endswith('main.pea')

def test_pea_lib_runtime_install_and_import():
    """Phase 41: import a path-based dependency library in an app."""
    import tempfile, os

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, 'myapp')
        os.makedirs(project_dir)

        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Initialize an app project
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'init', 'myapp'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        # Initialize a library project (already creates src/mylib.pea with exports)
        lib_dir = os.path.join(tmpdir, 'mylib')
        os.makedirs(lib_dir)
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', lib_dir
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        # Write a main app file that imports mylib via relative path
        main_pea = os.path.join(project_dir, 'main.pea')
        lib_src = os.path.join(tmpdir, 'mylib', 'src', 'mylib.pea')
        rel = os.path.relpath(lib_src, project_dir).replace(os.sep, '/')
        with open(main_pea, 'w') as f:
            f.write(f'import "./{rel}" as mylib\n')
            f.write('print mylib.add(2, 3)\n')

        # Run with the app project
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'run', 'main.pea'
        ], capture_output=True, text=True, cwd=project_dir, env=env)
        assert result.returncode == 0, result.stderr

def test_pea_lib_runtime_installed_modules():
    """Phase 41: library installed into .pea_modules is resolvable at runtime."""
    from pealang.package_manager import init_manifest
    import tempfile, os, shutil

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, 'myapp')
        os.makedirs(project_dir)

        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Initialize app project
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'init', 'myapp'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        # Manually install a library into .pea_modules using library template
        lib_dir = os.path.join(tmpdir, 'mylib')
        os.makedirs(lib_dir)
        init_manifest(lib_dir, 'mylib')
        main_pea = os.path.join(lib_dir, 'src', 'mylib.pea')
        os.makedirs(os.path.dirname(main_pea), exist_ok=True)
        with open(main_pea, 'w') as f:
            f.write('function add(a, b) {\n    return a + b\n}\nexport add\n')

        pea_modules = os.path.join(project_dir, '.pea_modules', 'mylib')
        os.makedirs(pea_modules, exist_ok=True)
        shutil.copy(main_pea, os.path.join(pea_modules, 'main.pea'))

        # create pea.toml in .pea_modules/mylib so resolve_module finds entry
        pea_toml = os.path.join(pea_modules, 'pea.toml')
        with open(pea_toml, 'w') as f:
            f.write('[project]\nname = "mylib"\nversion = "0.1.0"\nentry = "main.pea"\n')

        from pealang.project import resolve_module
        result = resolve_module('mylib', project_dir, project_dir, {})
        assert result.exists()
        assert str(result).endswith('main.pea')

if __name__ == '__main__':
    test_pea_lib_runtime_resolve_module()
    test_pea_lib_runtime_install_and_import()
    test_pea_lib_runtime_installed_modules()
    print("All library runtime tests passed!")