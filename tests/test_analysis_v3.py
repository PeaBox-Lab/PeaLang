from pealang import execute


def run(src):
    out = []
    execute(src, output=out.append, source_name="analysis.pea")
    return out


def test_analysis_charts():
    src = """
let data = [{"label":"A","v":3},{"label":"B","v":7}]
let b = analysis.bar_chart(data, "label", "v")
let l = analysis.line_chart(data, "v")
print b
print l
"""
    out = run(src)
    assert "A |" in out[0]
    assert "B |" in out[0]
    assert "*" in out[1]

