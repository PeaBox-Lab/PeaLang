from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="lang.pea")
    return out


def test_collection_builtins_v105():
    src = r'''
print coalesce(null, null, 7)
print repeat("x", 3)
print pluck([{"a":1},{"a":2}], "a")
print index_by([{"id":1,"n":"a"},{"id":2,"n":"b"}], "id")[2]["n"]
print sort_by([{"v":2},{"v":1}], "v")[0]["v"]
print find([1,2,3], function(x){ return x > 1 })
print find_index([1,2,3], function(x){ return x == 2 })
print times(3, function(i){ return i * 2 })
'''
    out = run(src)
    assert out == ["7", '["x", "x", "x"]', "[1, 2]", "b", "1", "2", "1", "[0, 2, 4]"]
