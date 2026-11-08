from pealang import execute


def run(src, **kw):
    out = []
    execute(src, output=out.append, source_name="comp.pea", **kw)
    return out


def test_list_comprehension_basic():
    src = """
let xs = [1,2,3,4]
print [x * 2 for x in xs]
print [x for x in xs if x % 2 == 0]
"""
    out = run(src)
    assert out[0] == "[2, 4, 6, 8]"
    assert out[1] == "[2, 4]"


def test_comprehension_with_records():
    src = """
let xs = [1,2,3]
let out = [{"n": x, "sq": x * x} for x in xs if x > 1]
print out[0]["n"]
print out[1]["sq"]
"""
    out = run(src)
    assert out == ["2", "9"]

