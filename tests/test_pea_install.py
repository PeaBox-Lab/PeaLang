import subprocess, sys, os, tempfile
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_install_cli():
    """Phase 37: pea install CLI command."""
    # Create a temp project directory
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, 'test_project')
        os.makedirs(project_dir)
        
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')
        
        # Initialize a library project (creates pea.toml)
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', project_dir
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr
        
        # Install a library
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'install', 'testlib', '1.0.0'
        ], capture_output=True, text=True, cwd=project_dir, env=env)
        
        assert result.returncode == 0, result.stderr
        assert 'Installed: testlib' in result.stdout
        
        # Check that .pea_modules exists
        pea_modules_dir = os.path.join(project_dir, '.pea_modules')
        assert os.path.exists(pea_modules_dir)
        
        # Check that testlib directory exists inside .pea_modules
        testlib_dir = os.path.join(pea_modules_dir, 'testlib')
        assert os.path.exists(testlib_dir)


def test_pea_install_remote():
    """Phase 37: install_remote function."""
    from pealang.package_manager import install_remote
    import os, tempfile
    
    # Test basic install_remote functionality within a project
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, 'test_project')
        os.makedirs(project_dir)
        
        # Initialize a library project (creates pea.toml)
        from pealang.package_manager import init_manifest
        init_manifest(project_dir, 'test_project')
        
        # Change to project dir
        orig_cwd = os.getcwd()
        os.chdir(project_dir)
        try:
            result = install_remote('testlib', '1.0.0')
            assert result['name'] == 'testlib'
            assert result['version'] == '1.0.0'
            assert result['source'] == 'registry'
            assert result['installed'] is True
            
            # Check that .pea_modules directory exists
            pea_modules_dir = os.path.join(project_dir, '.pea_modules')
            dest_dir = os.path.join(pea_modules_dir, 'testlib')
            assert os.path.exists(pea_modules_dir)
            assert os.path.exists(dest_dir)
        finally:
            os.chdir(orig_cwd)