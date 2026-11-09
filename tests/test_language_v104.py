from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="lang.pea")
    return out


def test_list_dict_utils():
    src = r'''
print chunk([1,2,3,4,5], 2)
print flatten([[1],[2,[3]]], 2)
print uniq([1,1,2,2,3])
print pick({"a":1,"b":2,"c":3}, ["a","c"])
print omit({"a":1,"b":2,"c":3}, ["b"])
print clamp(10, 0, 5)
let e = b64encode("hi")
print b64decode(e)
print len(uuid()) > 10
'''
    out = run(src)
    assert out[0] == "[[1, 2], [3, 4], [5]]"
    assert out[1] == "[1, 2, 3]"
    assert out[2] == "[1, 2, 3]"
    assert '"a": 1' in out[3] and '"c": 3' in out[3]
    assert '"b"' not in out[4]
    assert out[5] == "5"
    assert out[6] == "hi"
    assert out[7] == "true"
