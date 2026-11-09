from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_v110():
    src = r'''
let d = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
print analysis.drop_columns(d, ["b"])[0]["a"]
print analysis.keep_columns(d, ["a"])[1]["a"]
print analysis.assign([{"a": 1}], {"b": 9})[0]["b"]
print analysis.round_col([{"v": 1.234}], "v", 2)[0]["v"]
print analysis.abs_col([{"v": -5}], "v")[0]["v"]
print analysis.variance([{"v": 1}, {"v": 2}, {"v": 3}], "v")
print analysis.std([{"v": 1}, {"v": 2}, {"v": 3}], "v") > 0
print analysis.covariance([{"x": 1, "y": 2}, {"x": 2, "y": 4}, {"x": 3, "y": 6}], "x", "y") > 0
print analysis.idxmax([{"v": 1}, {"v": 9}, {"v": 3}], "v")
print analysis.idxmin([{"v": 1}, {"v": 9}, {"v": 3}], "v")
'''
    out = run(src)
    assert out == ["1", "3", "9", "1.23", "5", "1", "true", "true", "1", "0"]
