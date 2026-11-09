from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_v106():
    src = r'''
print analysis.ffill([{"v":1},{"v":null},{"v":3}], "v")[1]["v"]
print analysis.dropna([{"v":1},{"v":null},{"v":3}], "v")[1]["v"]
print analysis.cast([{"v":"2"}], "v", "int")[0]["v"]
let ct = analysis.crosstab([{"r":"a","c":"x"},{"r":"a","c":"x"},{"r":"b","c":"x"}], "r", "c")
print ct["a"]["x"]
print ct["b"]["x"]
'''
    out = run(src)
    assert out == ["1", "3", "2", "2", "1"]
