from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_transformations():
    src = '''
let data = [{"name":"Ada","score":91,"g":"a"},{"name":"Linus","score":84,"g":"a"},{"name":"Ada","score":91,"g":"a"}]
let d = analysis.drop_duplicates(data)
print len(d)
let r = analysis.rename(d, {"name":"person"})
print r[0]["person"]
let q = analysis.query(r, "score", ">", 85)
print len(q)
let s = analysis.summary(r)
print s
'''
    out = run(src)
    assert out[0] == "2"
    assert out[1] == "Ada"
    assert out[2] == "1"
    assert "Rows: 2" in out[3]


def test_analysis_advanced():
    src = '''
let data = [{"v":1},{"v":null},{"v":3}]
let f = analysis.fillna(data, 0, "v")
print f[1]["v"]
let c = analysis.cumsum([{"v":1},{"v":2},{"v":3}], "v")
print c[2]["v_cumsum"]
let u = analysis.unique([{"g":"a"},{"g":"b"},{"g":"a"}], "g")
print u
let q = analysis.quantile([{"v":1},{"v":2},{"v":3},{"v":4}], "v", 0.5)
print q
let a = analysis.add_column([{"x":2},{"x":3}], "y", function(r){ return r["x"] * 10 })
print a[1]["y"]
'''
    out = run(src)
    assert out == ["0", "6", '["a", "b"]', "2.5", "30"]
