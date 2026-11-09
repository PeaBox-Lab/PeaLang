from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_v109():
    src = r'''
let s = analysis.shift([{"v": 1}, {"v": 2}, {"v": 3}], "v", 1)
print s[0]["v"]
print s[1]["v"]
let l = analysis.lead([{"v": 1}, {"v": 2}, {"v": 3}], "v", 1)
print l[0]["v"]
print analysis.cummax([{"v": 1}, {"v": 3}, {"v": 2}], "v")[2]["v_cummax"]
print analysis.cummin([{"v": 3}, {"v": 1}, {"v": 2}], "v")[2]["v_cummin"]
print analysis.cumprod([{"v": 2}, {"v": 3}, {"v": 4}], "v")[2]["v_cumprod"]
let oh = analysis.one_hot([{"c": "a"}, {"c": "b"}, {"c": "a"}], "c")
print oh[0]["c_a"]
print oh[0]["c_b"]
let sp = analysis.split_column([{"p": "a,b"}], "p", ",", ["x", "y"])
print sp[0]["x"]
print sp[0]["y"]
'''
    out = run(src)
    assert out == ["null", "1", "2", "3", "1", "24", "1", "0", "a", "b"]
