from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_v112():
    src = r'''
let d = [{"v": 1}, {"v": 2}, {"v": 3}]
print analysis.rolling_std(d, "v", 3)[2]["v_rolling_std"] > 0
print analysis.expanding_sum(d, "v")[2]["v_expanding_sum"]
print analysis.expanding_max([{"v": 1}, {"v": 3}, {"v": 2}], "v")[2]["v_expanding_max"]
print analysis.expanding_min([{"v": 3}, {"v": 1}, {"v": 2}], "v")[2]["v_expanding_min"]
let s = analysis.sample_frac([{"v": 1}, {"v": 2}, {"v": 3}, {"v": 4}], 0.5, 7)
print len(s)
let e = analysis.ewm_mean([{"v": 10}, {"v": 20}], "v", 0.5)
print e[1]["v_ewm"]
let z = analysis.standardize([{"v": 1}, {"v": 2}, {"v": 3}], "v")
print z[1]["v_z"]
'''
    out = run(src)
    assert out == ["true", "6", "3", "1", "2", "15", "0"]
