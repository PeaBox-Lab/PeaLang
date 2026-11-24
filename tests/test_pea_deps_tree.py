import subprocess, sys, os, tempfile
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def test_pea_deps_tree():
    """Phase 47: pea deps --tree shows dependency tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')

        # Init a library project
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'init', '--template', 'library', 'treetest'],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0

        project_dir = os.path.join(tmpdir, 'treetest')

        # Create nested libraries
        lib1 = os.path.join(tmpdir, 'lib1')
        os.makedirs(lib1, exist_ok=True)
        with open(os.path.join(lib1, 'main.pea'), 'w') as f:
            f.write('function add(a, b) { return a + b }\n')
        with open(os.path.join(lib1, 'pea.toml'), 'w') as f:
            f.write('[project]\nname = "lib1"\nversion = "0.1.0"\nentry = "main.pea"\n')
            f.write('[dependencies]\n')
            f.write('"lib2" = { path = "../lib2" }\n')

        lib2 = os.path.join(tmpdir, 'lib2')
        os.makedirs(lib2, exist_ok=True)
        with open(os.path.join(lib2, 'main.pea'), 'w') as f:
            f.write('function mul(a, b) { return a * b }\n')
        with open(os.path.join(lib2, 'pea.toml'), 'w') as f:
            f.write('[project]\nname = "lib2"\nversion = "0.2.0"\nentry = "main.pea"\n')

        # Write project pea.toml
        pea_toml = os.path.join(project_dir, 'pea.toml')
        with open(pea_toml, 'w') as f:
            f.write('[project]\nname = "treetest"\nversion = "0.1.0"\nentry = "src/treetest.pea"\n')
            f.write('[dependencies]\n')
            f.write('"lib1" = { path = "../lib1" }\n')

        # Run deps --tree
        result = subprocess.run([sys.executable, '-m', 'pealang.cli', 'deps', '--tree', project_dir],
                                capture_output=True, text=True, cwd=tmpdir, env=env)
        assert result.returncode == 0, result.stderr

        tree = json.loads(result.stdout)
        assert len(tree) == 1
        assert tree[0]['name'] == 'lib1'
        assert 'children' in tree[0]
        assert len(tree[0]['children']) == 1
        assert tree[0]['children'][0]['name'] == 'lib2'
        # lib2 has no children -> empty list
        assert tree[0]['children'][0].get('children', []) == []

if __name__ == '__main__':
    test_pea_deps_tree()
    print("All deps tree tests passed!")