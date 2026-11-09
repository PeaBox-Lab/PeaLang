from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_v111():
    src = r'''
let d = [{"v": 1}, {"v": 3}, {"v": 5}]
print analysis.mean_col(d, "v")
print analysis.sum_col(d, "v")
print analysis.min_col(d, "v")
print analysis.max_col(d, "v")
print analysis.median_col(d, "v")
print analysis.expanding_mean(d, "v")[2]["v_expanding_mean"]
let jl = analysis.to_jsonl([{"a": 1}, {"a": 2}])
print analysis.from_jsonl(jl)[1]["a"]
print analysis.skew([{"v": 1}, {"v": 2}, {"v": 3}, {"v": 10}], "v") != null
print analysis.kurtosis([{"v": 1}, {"v": 2}, {"v": 3}, {"v": 4}, {"v": 5}], "v") != null
print analysis.corr([{"x": 1, "y": 2}, {"x": 2, "y": 4}], "x", "y")
'''
    out = run(src)
    assert out == ["3", "9", "1", "5", "3", "3", "2", "true", "true", "1"]
