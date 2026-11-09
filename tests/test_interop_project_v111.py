import os
import tempfile
from pealang import execute
from pealang.project import TEMPLATES


def test_interop_v111():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "f.txt").replace("\\", "/")
    src = f'''
interop.touch("{p}")
print interop.exists("{p}")
interop.write_text("{p}", "a\\nb\\nc")
print interop.head_file("{p}", 2)[1]
print interop.tail_file("{p}", 1)[0]
print interop.expanduser("~") != null
let e = interop.env_all()
print e != null
'''
    out = []
    execute(src, output=out.append, source_name="interop.pea")
    assert out[:3] == ["true", "b", "c"]
    assert out[3] == "true"
    assert out[4] == "true"


def test_etl_template_v111():
    assert "etl" in TEMPLATES
    assert "analysis.from_json" in TEMPLATES["etl"]
