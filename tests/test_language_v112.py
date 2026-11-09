from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="lang.pea")
    return out


def test_v112_builtins():
    src = r'''
print gcd(12, 8)
print lcm(4, 6)
print sign(-5)
print sign(0)
print is_even(4)
print is_odd(3)
print lerp(0, 10, 0.5)
print rotate([1, 2, 3, 4], 1)
print interleave([1, 2], [3, 4], [5, 6])
print windows([1, 2, 3, 4], 2)
print dedupe_by([{"id": 1}, {"id": 1}, {"id": 2}], "id")[1]["id"]
print assoc({"a": 1}, "b", 2)["b"]
print dissoc({"a": 1, "b": 2}, "b")
print rename_keys({"a": 1}, {"a": "x"})["x"]
print format_number(3.14159, 2)
print between(5, 1, 10)
'''
    out = run(src)
    assert out == [
        "4", "12", "-1", "0", "true", "true", "5", "[4, 1, 2, 3]",
        "[1, 3, 5, 2, 4, 6]", "[[1, 2], [2, 3], [3, 4]]", "2", "2",
        '{"a": 1}', "1", "3.14", "true",
    ]
