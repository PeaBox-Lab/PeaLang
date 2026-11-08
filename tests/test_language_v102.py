from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="lang.pea")
    return out


def test_membership_and_builtins():
    src = '''
print 2 in [1,2,3]
print 4 not in [1,2,3]
print "ell" in "hello"
print sorted([3,1,2])
print sum([1,2,3])
print any([false, true])
print all([true, true])
let pairs = [[1,10],[2,20]]
print [v for [k,v] in pairs if k > 1]
'''
    out = run(src)
    assert out == ["true", "true", "true", "[1, 2, 3]", "6", "true", "true", "[20]"]


def test_dict_comprehension_and_items():
    src = '''
let d = {"a": 1, "b": 2}
let sq = {k: v * v for [k,v] in items(d)}
print sq["a"]
print sq["b"]
let m = list(map(function(x){ return x*2 }, [1,2,3]))
print m
let f = list(filter(function(x){ return x > 1 }, [1,2,3]))
print f
'''
    out = run(src)
    assert out == ["1", "4", "[2, 4, 6]", "[2, 3]"]


def test_enumerate_zip_reversed():
    src = '''
print list(enumerate(["a","b"]))
print list(zip([1,2],[3,4]))
print list(reversed([1,2,3]))
'''
    out = run(src)
    assert out[0] == '[[0, "a"], [1, "b"]]'
    assert out[1] == "[[1, 3], [2, 4]]"
    assert out[2] == "[3, 2, 1]"
