import os
import tempfile
from pealang import execute


def test_interop_v109():
    d = tempfile.mkdtemp()
    src_path = os.path.join(d, "a.txt").replace("\\", "/")
    dst_path = os.path.join(d, "b.txt").replace("\\", "/")
    dpath = d.replace("\\", "/")
    src = f'''
interop.write_text("{src_path}", "hello")
interop.copy_file("{src_path}", "{dst_path}")
print interop.read_text("{dst_path}")
let st = interop.stat("{src_path}")
print st["is_file"]
print st["size"] > 0
let names = interop.list_dir("{dpath}")
print len(names) >= 2
print len(interop.hash_file("{src_path}")) == 64
print interop.remove_file("{dst_path}")
print interop.exists("{dst_path}")
'''
    out = []
    execute(src, output=out.append, source_name="interop.pea")
    assert out == ["hello", "true", "true", "true", "true", "true", "false"]
