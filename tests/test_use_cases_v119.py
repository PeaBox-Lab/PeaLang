from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def test_trees_forests_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "15_trees_forests.pea"
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    assert out == [
        "tree r2: 0.968",
        "tree rmse: 0.221",
        "forest r2: 0.986",
        "forest rmse: 0.148",
        "forest oob r2: 0.962",
        "class accuracy: 0.967",
        "class oob: 0.933",
        "top feature: b",
        "tree accuracy: 0.917",
        "tree top: b",
        "tree guess: [0, 1]",
    ]
