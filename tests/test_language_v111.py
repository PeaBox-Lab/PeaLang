from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="lang.pea")
    return out


def test_v111_builtins():
    src = r'''
let g = group_by([{"t": "a", "v": 1}, {"t": "a", "v": 2}, {"t": "b", "v": 3}], "t")
print len(g["a"])
print g["a"][1]["v"]
print frequencies(["x", "x", "y"])["x"]
print scan([1, 2, 3], function(a, b){ return a + b }, 0)
print hex_decode(hex_encode("hi"))
print ensure_int("9", 0)
print ensure_float("1.5", 0)
print ensure_str(null, "x")
print pipe(2, function(x){ return x + 1 }, function(x){ return x * 3 })
print apply(function(a, b){ return a + b }, [2, 3])
'''
    out = run(src)
    assert out == ["2", "2", "2", "[1, 3, 6]", "hi", "9", "1.5", "x", "9", "5"]
