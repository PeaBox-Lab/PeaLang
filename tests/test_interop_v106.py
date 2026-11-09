import os, tempfile
from pealang import execute


def test_interop_file_helpers():
    d = tempfile.mkdtemp()
    path = os.path.join(d, "t.json").replace("\\", "/")
    src = f'''
interop.write_json("{path}", {{"a": 1}})
let x = interop.read_json("{path}")
print x["a"]
interop.write_text("{path}.txt", "hello")
print interop.read_text("{path}.txt")
'''
    out = []
    execute(src, output=out.append, source_name="interop.pea")
    assert out == ["1", "hello"]
