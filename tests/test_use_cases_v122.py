from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def test_model_interpretation_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "18_model_interpretation.pea"
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    assert out == [
        "reg top: x",
        "reg score: 2.123",
        "reg baseline: 1",
        "reg curves: 1",
        "reg grid: 7",
        "reg rise: true",
        "cls task: classification",
        "cls top: signal",
        "cls score: 0.458",
        "cls noise: 0",
        "cls classes: [0, 1]",
        "cls low: 0.112",
        "cls high: 0.844",
        "stats top: signal",
        "stats curve: signal",
    ]
