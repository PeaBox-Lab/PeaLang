import subprocess, sys, os, tempfile
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_publish_dry_run_cli():
    """Phase 49: pea publish --dry-run builds the library package without uploading."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Initialize a library project
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testdryrun'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testdryrun')
        # Build the library (no publish needed, just ensure .pelib exists)
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'lib', 'build', project_dir
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        # Run publish with --dry-run
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'publish', project_dir, '--dry-run'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        # Verify dry-run output
        output = result.stdout.strip()
        assert 'Dry-run: built library at' in output
        assert 'sha256' in output

def test_pea_lib_publish_dry_run_cli():
    """Phase 49: pea lib publish --dry-run builds the library package without uploading."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Create library project via init
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'testdryrun2'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'testdryrun2')
        # Build the library (ensure .pelib exists)
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'lib', 'build', project_dir
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        # Run lib publish with --dry-run
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'lib', 'publish', project_dir, '--dry-run'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        # Verify dry-run output
        output = result.stdout.strip()
        assert 'Dry-run: built library at' in output
        assert 'sha256' in output

if __name__ == '__main__':
    test_pea_publish_dry_run_cli()
    test_pea_lib_publish_dry_run_cli()
    print("All dry-run publish tests passed!")