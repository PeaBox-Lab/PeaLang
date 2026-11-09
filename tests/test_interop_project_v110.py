import os
import tempfile
from pealang import execute
from pealang.project import TEMPLATES


def test_interop_v110():
    d = tempfile.mkdtemp()
    dpath = d.replace("\\", "/")
    src = f'''
interop.write_text("{dpath}/a.txt", "one\\ntwo")
print interop.readlines("{dpath}/a.txt")[1]
interop.writelines("{dpath}/b.txt", ["x", "y"])
print interop.readlines("{dpath}/b.txt")[0]
let w = interop.walk("{dpath}")
print len(w) >= 2
let tf = interop.tempfile("pea_test_", ".tmp", "hi")
print interop.read_text(tf)
interop.remove_file(tf)
'''
    out = []
    execute(src, output=out.append, source_name="interop.pea")
    assert out == ["two", "x", "true", "hi"]


def test_project_api_template_v110():
    assert "api" in TEMPLATES
    assert "web.health()" in TEMPLATES["api"]
    assert "web.envelope(" in TEMPLATES["api"]
