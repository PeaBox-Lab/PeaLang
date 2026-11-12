from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def test_model_selection_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "17_model_selection.pea"
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    assert out == [
        'reg best: {"learning_rate": 0.2, "max_depth": 3, "n_estimators": 20}',
        "reg score: 0.968",
        "reg candidates: 8",
        'reg features: ["x"]',
        "reg cv: 0.968 +/- 0.024",
        'cls best: {"max_depth": 3, "n_estimators": 10}',
        "cls score: 0.838",
        "cls candidates: 4",
        "cls task: classification",
        "cls top: a",
        "cls guess: [0, 1]",
    ]
