import subprocess, sys, os, tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_quality_cli():
    """Phase 39: pea quality CLI command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, 'test_project')
        os.makedirs(project_dir)

        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Initialize a library project via CLI (creates full structure incl [library] section)
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', project_dir
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        # Run quality check
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'quality', project_dir
        ], capture_output=True, text=True, cwd=tmpdir, env=env)

        assert result.returncode == 0
        out = result.stdout.lower()
        assert 'ok' in out or 'issues' in out

def test_quality_check_function():
    """Phase 39: quality_check() function with incomplete project."""
    from pealang.package_manager import quality_check, init_manifest
    import tempfile, os

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, 'test_project')
        os.makedirs(project_dir)

        # Initialize a basic project (no library section, no README, no LICENSE)
        init_manifest(project_dir, 'test_project')

        result = quality_check(project_dir)
        assert isinstance(result, dict)
        assert 'ok' in result
        assert 'issues' in result
        assert len(result['issues']) > 0
        assert result['name'] == 'test_project'
        assert result['version'] == '0.1.0'

def test_quality_check_valid_project():
    """Phase 39: quality_check with full library project (all files present)."""
    from pealang.package_manager import quality_check
    import subprocess, sys, os

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, 'test_project')
        os.makedirs(project_dir)

        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Initialize a library project via CLI (creates everything including README, LICENSE)
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', project_dir
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        result = quality_check(project_dir)
        assert result['ok'] is True
        assert len(result['issues']) == 0

if __name__ == '__main__':
    test_pea_quality_cli()
    test_quality_check_function()
    test_quality_check_valid_project()
    print("All quality tests passed!")