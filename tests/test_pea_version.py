import subprocess, sys, os, tempfile
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_version_json():
    """Phase 42: pea version --json prints version JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'version', '--json'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0
        out = json.loads(result.stdout)
        assert out['version'] == '5.3.0'

def test_pea_version_default():
    """Phase 42: pea version without args prints version."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'version'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0
        assert 'PeaLang 5.3.0' in result.stdout

def test_pea_version_project():
    """Phase 42: pea version <path> prints project version from pea.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, 'myproj')
        os.makedirs(project_dir)
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Initialize a project
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', 'myproj'],
                                capture_output=True, text=True, cwd=project_dir, env=env)
        assert result.returncode == 0

        # Write pea.toml with version
        pea_toml = os.path.join(project_dir, 'pea.toml')
        with open(pea_toml, 'w') as f:
            f.write('[project]\nname = "myproj"\nversion = "0.1.0"\nentry = "main.pea"\n')

        # Check version via CLI
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'version', project_dir],
                                capture_output=True, text=True, cwd=project_dir, env=env)
        assert result.returncode == 0
        assert 'Project "myproj" version: 0.1.0' in result.stdout

if __name__ == '__main__':
    test_pea_version_json()
    test_pea_version_default()
    test_pea_version_project()
    print("All version tests passed!")