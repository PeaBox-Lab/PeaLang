from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_rolling_variants():
    src = r'''
let d = [{"v": 1}, {"v": 2}, {"v": 3}]
print analysis.rolling_sum(d, "v", 2)[1]["v_rolling_sum"]
print analysis.rolling_min(d, "v", 2)[2]["v_rolling_min"]
print analysis.rolling_max(d, "v", 2)[2]["v_rolling_max"]
print analysis.rolling_median(d, "v", 3)[2]["v_rolling_median"]
print analysis.rolling_var(d, "v", 2)[1]["v_rolling_var"] > 0
'''
    assert run(src) == ["3", "2", "3", "2", "true"]


def test_expanding_variants():
    src = r'''
let d = [{"v": 1}, {"v": 2}, {"v": 3}]
print analysis.expanding_std(d, "v")[2]["v_expanding_std"] > 0
print analysis.expanding_var(d, "v")[2]["v_expanding_var"] > 0
print analysis.expanding_median(d, "v")[2]["v_expanding_median"]
'''
    assert run(src) == ["true", "true", "2"]


def test_qcut_and_factorize():
    src = r'''
let d = [{"v": 1}, {"v": 2}, {"v": 3}, {"v": 4}]
let q = analysis.qcut(d, "v", 2)
print q[0]["v_qcut"]
print q[3]["v_qcut"]
let ql = analysis.qcut(d, "v", 2, ["low", "high"])
print ql[3]["v_qcut"]
let f = analysis.factorize([{"c": "x"}, {"c": "y"}, {"c": "x"}], "c")
print f["codes"]
print f["uniques"]
'''
    assert run(src) == ["0", "1", "high", "[0, 1, 0]", '["x", "y"]']


def test_missing_and_column_transforms():
    src = r'''
let d = [{"v": 1}, {"v": null}, {"v": 3}]
print analysis.interpolate(d, "v")[1]["v"]
let m = analysis.mask([{"v": 1}, {"v": 5}], "v", function(x) { return x > 3 }, 0)
print m[1]["v"]
let t = analysis.transform([{"v": 1}, {"v": 2}], "v", function(x) { return x * 10 })
print t[1]["v"]
let w = analysis.winsorize([{"v": 1}, {"v": 2}, {"v": 100}], "v", 0.0, 0.5)
print w[2]["v"] < 100
'''
    assert run(src) == ["2", "0", "20", "true"]


def test_frame_introspection_and_aggregation():
    src = r'''
let d = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}, {"a": null, "b": "x"}]
print analysis.info(d)["rows"]
print analysis.memory_usage(d)["bytes"] > 0
print analysis.missing_summary(d)[0]["missing"]
print analysis.select_dtypes(d, "number")[0]["a"]
print analysis.reset_index([{"a": 1}])[0]["index"]
print analysis.set_index([{"k": 2}, {"k": 1}], "k")[0]["k"]
let a = analysis.agg(d, "a", ["count", "mean", "sum"])
print a["count"]
print a["mean"]
print a["sum"]
'''
    assert run(src) == ["3", "true", "1", "1", "0", "1", "2", "1.5", "3"]


def test_pivot_group_merge_and_dates():
    src = r'''
let d = [{"g": "a", "k": "x", "v": 1}, {"g": "a", "k": "y", "v": 2}, {"g": "b", "k": "x", "v": 3}]
let p = analysis.pivot_table(d, "g", "k", "v", "sum")
print len(p)
print p[0]["x"]
print p[0]["y"]
print len(analysis.group_by_multi(d, ["g", "k"], "v", "sum"))
let m = analysis.merge_multi([{"id": 1, "a": 10}], [{"id": 1, "b": 20}], "id")
print m[0]["b"]
print analysis.corr_spearman([{"x": 1, "y": 2}, {"x": 2, "y": 4}, {"x": 3, "y": 6}], "x", "y")
print len(analysis.date_range("2026-01-01", "2026-01-03"))
'''
    assert run(src) == ["2", "1", "2", "3", "20", "1", "3"]


def test_describe_all():
    src = r'''
let d = [{"a": 1, "b": 10}, {"a": 2, "b": 20}]
let s = analysis.describe_all(d)
print s["a"]["mean"]
print s["b"]["max"]
'''
    assert run(src) == ["1.5", "20"]
