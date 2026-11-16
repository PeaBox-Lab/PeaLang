"""help() builtin and catch frame/trace access."""

from pealang import execute, PeaError
import pytest


def run(src):
    out = []
    try:
        execute(src, output=out.append, source_name="t.pea")
        return ("ok", out)
    except PeaError as e:
        return ("err", e)


def test_help_overview():
    status, out = run('print help()')
    assert status == "ok"
    text = out[0]
    assert text.startswith("PeaLang help")


def test_help_topic():
    status, out = run('print help("match")')
    assert status == "ok"
    assert "Pattern matching" in out[0]


def test_help_unknown_topic():
    status, out = run('print help("bogus")')
    assert status == "ok"
    assert "Unknown topic" in out[0]
    assert "match" in out[0]


def test_catch_frames_and_trace():
    src = """function deep() {
    return missing_var
}
function l2() { return deep() }
function l1() { return l2() }
function l0() { return l1() }
try {
    l0()
} catch e {
    print e["frames"] != null
    print len(e["frames"])
    print help("x")
}"""
    status, out = run(src)
    assert status == "ok"
    assert out[0] == "true"
    assert out[1] == "4"
    assert "Unknown topic" in out[2]


def test_catch_trace_names():
    src = """function a() {
    throw 'boom'
}
function b() {
    return a()
}
try {
    b()
} catch e {
    print e["trace"]
}"""
    status, out = run(src)
    assert status == "ok"
    trace = out[0]
    assert "in b" in trace
    assert "in a" in trace


def test_catch_string_frames_are_function_names():
    src = """function outer() {
    return missing_var
}
try {
    outer()
} catch e {
    print len(e["frames"])
}"""
    status, out = run(src)
    assert status == "ok"
    assert out[0] == "1"