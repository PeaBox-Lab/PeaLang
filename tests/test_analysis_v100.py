from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_profile_and_describe():
    src = """
let data = [{"name": "Ada", "score": 91}, {"name": "Linus", "score": 84}]
let p = analysis.profile(data)
print p["rows"]
let d = analysis.describe(data, "score")
print d["score"]["mean"]
"""
    out = run(src)
    assert out == ["2", "87.5"]


def test_analysis_clean_normalize_pivot():
    src = """
let data = [{"x": 1, "g": "a"}, {"x": null, "g": "b"}, {"x": 3, "g": "a"}]
let cleaned = analysis.clean_missing(data, "drop")
print len(cleaned)
let norm = analysis.normalize([{"v": 0}, {"v": 10}], "v", "minmax")
print norm[1]["v"]
let piv = analysis.pivot([{"g":"a","k":"x","v":1},{"g":"a","k":"x","v":2}], "g", "k", "v", "sum")
print piv["a"]["x"]
"""
    out = run(src)
    assert out[0] == "2"
    assert out[1] == "1"
    assert out[2] == "3"


def test_analysis_markdown():
    src = """
let p = analysis.profile([{"a": 1}])
print analysis.to_markdown(p)
"""
    out = run(src)
    assert "Data Profile" in out[0]

