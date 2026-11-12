from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def run_example(name, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    return out


def test_inference_report(tmp_path, monkeypatch):
    out = run_example("09_inference_report.pea", tmp_path, monkeypatch)
    assert out == [
        "mean ci: 74.23 .. 90.02",
        "cohens d: 1.67",
        "power: 0.807",
        "n per group: 63",
        "bh rejects first: true",
        "bonferroni second: 0.12",
        "r2: 0.9829",
        "terms: 3",
        "a p: 0.0042",
        "residual normality p: 0.773",
        "predicted: 4.809",
    ]


def test_forecasting_pipeline(tmp_path, monkeypatch):
    out = run_example("10_forecasting_pipeline.pea", tmp_path, monkeypatch)
    assert out == [
        "acf1: -0.317",
        "pacf1: -0.317",
        "ljung-box p: 0.0017",
        "seasonal diff length: 9",
        "forecast: 13.75, 23.83",
        "seasonal pattern: -8.5, 8.5",
        "changepoint: 3",
        "adf stationary: false",
    ]
