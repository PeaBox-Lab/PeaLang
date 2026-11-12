from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def test_feature_pipeline_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "20_feature_pipeline.pea"
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    assert out == [
        "task: classification",
        "used: 120",
        'outputs: ["region=east", "region=north", "region=south", "plan=basic", "plan=pro", "tenure", "spend"]',
        "train accuracy: 0.983",
        "top: spend",
        "probes: [1, 0, 1]",
        "positive: [0.922, 0.121, 0.787]",
        "columns: 7",
        "imputed: 20",
        "categorical: 2",
        'encoded names: ["region=east", "region=north", "region=south", "plan=basic", "plan=pro", "tenure", "spend"]',
    ]
