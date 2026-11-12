from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def test_gradient_boosting_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "16_gradient_boosting.pea"
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    assert out == [
        "reg train r2: 1",
        "reg test r2: 0.983",
        "reg test rmse: 1.391",
        "reg top: x",
        "binary accuracy: 0.7",
        "binary auc: 0.879",
        "binary log loss: 0.586",
        "binary top: a",
        "binary guess: [0, 1]",
        "multi train accuracy: 0.91",
        "multi test accuracy: 0.826",
        "multi classes: [0, 1, 2]",
        "multi top: a",
        "multi guess: [0, 1, 2]",
        "multi top prob: 1",
    ]
