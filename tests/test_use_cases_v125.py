from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def test_model_persistence_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "21_model_persistence.pea"
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    assert out == [
        "top: spend",
        "estimator: random_forest",
        "task: classification",
        "features: 3",
        "outputs: 6",
        "has preprocessor: true",
        "accuracy: 1",
        "probes: [1, 0, 0]",
        "same: true",
        "compact: true",
        "kept payload: true",
    ]
    saved = tmp_path / "churn_model.json"
    assert saved.exists()
    assert saved.read_text(encoding="utf-8").startswith(
        '{\n  "format": "pealang.model",'
    )
