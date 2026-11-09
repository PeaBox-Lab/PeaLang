from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_v108():
    src = r'''
let ex = analysis.explode([{"id": 1, "tags": ["a", "b"]}], "tags")
print len(ex)
print ex[1]["tags"]
let s = analysis.shape([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
print s["rows"]
print s["columns"]
print analysis.isna([{"v": 1}, {"v": null}], "v")
print analysis.notna([{"v": 1}, {"v": null}], "v")
let r = analysis.to_records([{"a": 1}])
print r[0]["a"]
let sc = analysis.str_contains([{"n": "Apple"}, {"n": "banana"}], "n", "app", false)
print len(sc)
let sr = analysis.str_replace([{"n": "a-b"}], "n", "-", "_")
print sr[0]["n"]
let sl = analysis.str_lower([{"n": "Hi"}], "n")
print sl[0]["n"]
'''
    out = run(src)
    assert out == ["2", "b", "2", "2", "1", "1", "1", "1", "a_b", "hi"]
