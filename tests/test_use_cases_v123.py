from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def test_class_imbalance_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "19_class_imbalance.pea"
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    assert out == [
        "train counts: [80, 25]",
        "train ratio: 3.2",
        "base accuracy: 0.733",
        "base balanced: 0.547",
        "base recall: 0.182",
        "smote added: 55",
        "smote counts: [80, 80]",
        "smote ratio: 1",
        "smote accuracy: 0.8",
        "smote balanced: 0.806",
        "smote recall: 0.818",
        "over rows: 160",
        "under rows: 50",
    ]
