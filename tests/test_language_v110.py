from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="lang.pea")
    return out


def test_v110_builtins():
    src = r'''
print min_by([{"v": 3}, {"v": 1}, {"v": 2}], "v")["v"]
print max_by([{"v": 3}, {"v": 1}, {"v": 2}], "v")["v"]
print without([1, 2, 3, 2], 2)
print xor([1, 2, 4], [2, 3])
print zip_object(["a", "b"], [1, 2])["b"]
print ensure_list(null)
print ensure_list(5)
print size(ensure_dict(null))
print ensure_dict(5)["value"]
print size({"a": 1, "b": 2})
print deep_equal({"a": [1]}, {"a": [1]})
print clone([1, 2])[0]
print nth([10, 20, 30], 1)
print nth([10, 20], 5, 99)
print initial([1, 2, 3])
print rest([1, 2, 3])
print random_choice([7]) == 7
'''
    out = run(src)
    assert out == [
        "1", "3", "[1, 3]", "[1, 4, 3]", "2", "[]", "[5]", "0", "5",
        "2", "true", "1", "20", "99", "[1, 2]", "[2, 3]", "true",
    ]
