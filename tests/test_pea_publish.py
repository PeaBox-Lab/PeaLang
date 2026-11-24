import subprocess, sys, os, tempfile, json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_publish_cli():
    """Phase 38: pea publish CLI command."""
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

        # Build the library (publish requires a token, so we test with --token dummy)
        result = subprocess.run([
            sys.executable, '-m', 'pealang.cli', 'publish', project_dir, '--token', 'dummy'
        ], capture_output=True, text=True, env=env)

        # Should fail because dummy token won't authenticate, but should at least
        # attempt to build and upload
        assert result.returncode == 1
        assert 'Upload failed' in result.stderr or 'Upload failed' in result.stdout or 'Error' in result.stdout


def test_pea_publish_remote():
    """Phase 38: publish() function in package_manager."""
    from pealang.package_manager import publish, init_manifest, load_pea_toml
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, 'test_project')
        os.makedirs(project_dir)

        # Initialize a library project
        init_manifest(project_dir, 'test_project')

        # Publish should build the library and return metadata
        result = publish(project_dir, registry='http://127.0.0.1:8788', token='dummy')

        assert result['name'] == 'test_project'
        assert result['version'] == '0.1.0'
        assert result['registry'] == 'http://127.0.0.1:8788'
        assert result['published'] is True
        assert 'sha256' in result
        assert len(result['sha256']) == 64  # SHA-256 hex digest
        assert os.path.exists(result['path'])


def test_pea_publish_invalid_path():
    """Phase 38: publish() with invalid path raises error."""
    from pealang.package_manager import publish
    from pealang.errors import PeaError
    import pytest

    with pytest.raises(PeaError):
        publish('/nonexistent/path')


if __name__ == '__main__':
    test_pea_publish_cli()
    test_pea_publish_remote()
    test_pea_publish_invalid_path()
    print("All tests passed!")