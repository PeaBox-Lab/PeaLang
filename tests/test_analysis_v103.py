from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_new_ops():
    src = r'''
let data = [{"v":1},{"v":5},{"v":3},{"v":2}]
print len(analysis.between(data, "v", 2, 4))
print analysis.mode([{"g":"a"},{"g":"a"},{"g":"b"}], "g")
print analysis.nunique([{"g":"a"},{"g":"a"},{"g":"b"}], "g")
print analysis.count([{"v":1},{"v":null},{"v":2}], "v")
let clipped = analysis.clip([{"v":-1},{"v":5},{"v":99}], "v", 0, 10)
print clipped[2]["v"]
let wide = [{"id":1,"a":10,"b":20}]
let m = analysis.melt(wide, ["id"], ["a","b"])
print len(m)
print m[0]["variable"]
'''
    out = run(src)
    assert out == ["2", "a", "2", "2", "10", "2", "a"]
