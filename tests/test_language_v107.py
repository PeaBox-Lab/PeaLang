from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="lang.pea")
    return out


def test_v107_builtins():
    src = r'''
print get_path({"a":{"b":[1,2]}}, "a.b")
print deep_merge({"a":{"x":1}}, {"a":{"y":2}})["a"]["y"]
print take([1,2,3,4], 2)
print drop([1,2,3,4], 2)
print first([9,8])
print last([9,8])
print partition([1,2,3,4], function(x){ return x%2==0 })[0]
print count_by(["a","a","b"])["a"]
'''
    out = run(src)
    assert out == ['[1, 2]', '2', '[1, 2]', '[3, 4]', '9', '8', '[2, 4]', '2']
