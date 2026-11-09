from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_v107():
    src = r'''
let d = [{"v":1},{"v":9},{"v":3}]
print analysis.nlargest(d, 2, "v")[0]["v"]
print analysis.nsmallest(d, 1, "v")[0]["v"]
let dup = analysis.duplicated([{"a":1},{"a":1},{"a":2}], ["a"])
print dup[1]["_duplicated"]
let w = analysis.pivot_wider([{"id":1,"k":"a","v":10},{"id":1,"k":"b","v":20}], "k", "v", ["id"])
print w[0]["a"]
print w[0]["b"]
'''
    out = run(src)
    assert out == ["9", "1", "true", "10", "20"]
