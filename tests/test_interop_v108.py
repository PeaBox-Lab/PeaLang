import os
import tempfile
from pealang import execute


def test_interop_path_helpers_v108():
    d = tempfile.mkdtemp().replace("\\", "/")
    p = os.path.join(d, "a.txt").replace("\\", "/")
    src = f'''
print interop.extname("{p}")
print interop.stem("{p}")
print interop.is_dir("{d}")
print interop.is_file("{p}")
print interop.join_path("{d}", "sub", "f.txt")
let info = interop.platform()
print info["system"]
print interop.cwd()
'''
    out = []
    execute(src, output=out.append, source_name="interop.pea")
    assert out[0] == ".txt"
    assert out[1] == "a"
    assert out[2] == "true"
    assert out[3] == "false"
    assert "sub" in out[4]
    assert out[5] in ("Windows", "Linux", "Darwin")
    assert len(out[6]) > 0
