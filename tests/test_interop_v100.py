import sys
from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="interop.pea")
    return out


def test_interop_python_bridge():
    src = """
let v = interop.call_python("math", "sqrt", 16)
print v
let cmd = interop.run("python", ["--version"])
print cmd["ok"]
"""
    out = run(src)
    assert out[0] == "4"
    assert out[1] == "true"


def test_interop_http_and_generate():
    src = """
let ts = interop.generate_typescript("http://localhost:8787")
print ts
"""
    out = run(src)
    assert "PEA_BASE_URL" in out[0]


def test_std_interop_available():
    src = """
let r = {"ok": true}
print r["ok"]
"""
    out = run(src)
    assert out == ["true"]

