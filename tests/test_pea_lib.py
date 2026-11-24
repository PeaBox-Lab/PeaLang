import subprocess, sys, os, tempfile
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_lib_new():
    """Phase 40: pea lib new creates a library project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'lib', 'new', 'mylib', '--template', 'library'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)

        assert result.returncode == 0, result.stderr
        assert 'pea.toml' in result.stdout
        assert 'mylib' in result.stdout.lower() or '.pea' in result.stdout

def test_pea_lib_build():
    """Phase 40: pea lib build builds a library package."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Create library project via init
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'mylib'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        # Build it
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'lib', 'build', 'mylib'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)

        assert result.returncode == 0, result.stderr
        assert 'sha256' in result.stdout

def test_pea_lib_quality():
    """Phase 40: pea lib quality runs quality check on library."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Create library project via init
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'mylib'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        # Run quality check
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'lib', 'quality', 'mylib'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)

        assert result.returncode == 0, result.stderr
        out = json.loads(result.stdout)
        assert 'ok' in out

def test_pea_lib_publish_invalid():
    """Phase 40: pea lib publish on invalid path errors cleanly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'lib', 'publish', tmpdir, '--token', 'dummy'
        ], capture_output=True, text=True, cwd=tmpdir, env=env)

        # Should fail (no pea.toml in tmpdir or upload will fail)
        assert result.returncode == 1

if __name__ == '__main__':
    test_pea_lib_new()
    test_pea_lib_build()
    test_pea_lib_quality()
    test_pea_lib_publish_invalid()
    print("All lib tests passed!")