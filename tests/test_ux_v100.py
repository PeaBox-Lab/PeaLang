from pealang import execute
import json


def run(src):
    out = []
    execute(src, output=out.append, source_name="ux.pea")
    return out


def test_ux_doctor():
    src = """
let d = ux.doctor()
print d["pealang"]
"""
    out = run(src)
    assert out[0] == "1.6.0"


def test_project_templates():
    import tempfile, os
    root = tempfile.mkdtemp()
    from pealang.project import init_project
    manifest = init_project(root, "demo", "webapp")
    assert os.path.exists(os.path.join(root, "main.pea"))
    with open(os.path.join(root, "main.pea")) as f:
        content = f.read()
    assert "web.app()" in content

