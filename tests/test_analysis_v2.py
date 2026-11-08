from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_group_join_sort():
    src = """
let data = [{"g":"a","v":1},{"g":"a","v":2},{"g":"b","v":3}]
let g = analysis.group_by(data, "g", "v", "sum")
print g["a"]
print g["b"]
let left = [{"id":1,"name":"Ada"},{"id":2,"name":"Linus"}]
let right = [{"id":1,"score":90},{"id":2,"score":80}]
let joined = analysis.join(left, right, "id")
print len(joined)
print analysis.to_csv(analysis.select(joined, "name", "score"))
"""
    out = run(src)
    assert out[0] == "3"
    assert out[1] == "3"
    assert out[2] == "2"
    assert "Ada,90" in out[3] or "Ada, 90" in out[3]


def test_analysis_filter_impute():
    src = """
let data = [{"x":1},{"x":null},{"x":3}]
let filled = analysis.impute(data, "x", "mean")
print filled[1]["x"]
let filtered = analysis.filter_rows(filled, function(r) { return r["x"] > 1 })
print len(filtered)
"""
    out = run(src)
    assert out[0] == "2"
    assert out[1] == "2"

