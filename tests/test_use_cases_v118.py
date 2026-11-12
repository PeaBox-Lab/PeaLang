from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def run_example(name, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    return out


def test_model_evaluation_example(tmp_path, monkeypatch):
    out = run_example("14_model_evaluation.pea", tmp_path, monkeypatch)
    assert out == [
        "train/test: 30/10",
        "holdout r2: 0.998",
        "holdout rmse: 0.215",
        "cv mean r2: 0.998",
        "accuracy: 0.9",
        "precision: 0.893",
        "recall: 0.893",
        "roc auc: 0.969",
        "log loss: 0.219",
        "x1*x2: 6",
        "codes: [0, 1, 0, 2]",
        "scaled: [[-1.0], [0.0], [1.0]]",
    ]
