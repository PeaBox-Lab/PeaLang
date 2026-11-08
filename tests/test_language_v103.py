from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="lang.pea")
    return out


def test_operators_and_helpers():
    src = r'''
print 2 ** 8
print int(9 / 2)
print get({"a":1}, "b", 42)
print has({"a":1}, "a")
print merge({"a":1}, {"b":2})["b"]
print trim("  hi  ")
print starts_with("hello", "he")
print contains("hello", "ell")
print safe(function(){ return missing_name }, 0)
print json_dump({"a":1})
'''
    out = run(src)
    assert out[0] == "256"
    assert out[1] == "4"
    assert out[2] == "42"
    assert out[3] == "true"
    assert out[4] == "2"
    assert out[5] == "hi"
    assert out[6] == "true"
    assert out[7] == "true"
    assert out[8] == "0"
    assert '"a": 1' in out[9] or '"a":1' in out[9]


def test_push_pop_slice():
    src = r'''
let a = [1,2]
push(a, 3)
print a
print pop(a)
print slice([1,2,3,4], 1, 3)
'''
    out = run(src)
    assert out == ["[1, 2, 3]", "3", "[2, 3]"]
