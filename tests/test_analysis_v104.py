from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_timeseries_and_schema():
    src = r'''
let d = [{"v":10},{"v":20},{"v":30}]
print analysis.rank(d,"v")[2]["v_rank"]
print analysis.diff(d,"v")[2]["v_diff"]
print analysis.pct_change(d,"v")[1]["v_pct"]
print analysis.rolling_mean(d,"v",2)[2]["v_rolling_mean"]
let s = analysis.schema([{"a":1,"b":"x","c":null}])
print s["a"]
print s["b"]
'''
    out = run(src)
    assert out == ["3", "10", "1", "25", "int", "string"]
