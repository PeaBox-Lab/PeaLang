import os, tempfile
from pealang import execute


def test_web_v107():
    src = r'''
print web.not_found()["status"]
print web.method_not_allowed(["GET"])["status"]
print web.url_join("/a/", "/b", "c")
'''
    out = []
    execute(src, output=out.append, source_name="web.pea")
    assert out == ["404", "405", "/a/b/c"]


def test_interop_v107():
    d = tempfile.mkdtemp().replace("\\", "/")
    src = f'''
print interop.exists("{d}")
print interop.basename("{d}/x.txt")
let p = interop.mkdir_p("{d}/sub/dir")
print interop.exists(p)
'''
    out = []
    execute(src, output=out.append, source_name="interop.pea")
    assert out == ["true", "x.txt", "true"]
