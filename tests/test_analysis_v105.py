from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_v105():
    src = r'''
let z = analysis.zscore([{"v":1},{"v":2},{"v":3}], "v")
print z[1]["v_z"]
let h = analysis.histogram([{"v":1},{"v":2},{"v":10}], "v", 2)
print len(h)
let c = analysis.cut([{"v":1},{"v":5},{"v":10}], "v", 2, ["low","high"])
print c[0]["v_bin"]
'''
    out = run(src)
    assert out[0] == "0"
    assert out[1] == "2"
    assert out[2] == "low"
