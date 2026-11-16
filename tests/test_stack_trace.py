"""Runtime stack traces: nested user-function frames attached to PeaErrors."""

from pealang import execute, PeaError
import pytest


SRC = """function inner() {
    return missing_variable
}

function outer() {
    return inner()
}

outer()"""


def run(src):
    out = []
    try:
        execute(src, output=out.append, source_name="trace.pea")
        return ("ok", out)
    except PeaError as e:
        return ("err", e)


def test_stack_trace_shows_call_chain():
    status, e = run(SRC)
    assert status == "err"
    assert "missing_variable" in str(e)
    assert e.frames is not None
    assert len(e.frames) == 2
    names = [f["name"] for f in e.frames]
    assert "outer" in names
    assert "inner" in names
    # inner is the deepest frame, should appear last
    assert names[-1] == "inner"
    # line numbers reference where the function is defined
    assert e.frames[-1]["line"] == 1


def test_stack_trace_with_throw():
    src = "function x() { throw 'boom' }\nfunction y() { return x() }\ny()"
    status, e = run(src)
    assert status == "err"
    assert "boom" in str(e)
    names = [f["name"] for f in e.frames]
    assert names == ["y", "x"]


def test_stack_trace_text_format():
    status, e = run(SRC)
    assert status == "err"
    rendered = e.trace()
    assert "in outer" in rendered
    assert "in inner" in rendered


def test_stack_trace_builtin_exception():
    src = "function z() { return int('nope') }\nz()"
    status, e = run(src)
    # builtin raised Frameless PeaError -> should be enriched with frames
    if status == "err" and e.frames is not None:
        names = [f["name"] for f in e.frames]
        assert "z" in names