from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def run_example(name, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    return out


def test_glm_survival(tmp_path, monkeypatch):
    out = run_example("11_glm_survival.pea", tmp_path, monkeypatch)
    assert out == [
        "logit slope: 0.237",
        "logit p: 0.225",
        "logit aic: 18.608",
        "poisson slope: 0.195",
        "poisson aic: 43.565",
        "ridge a: 2.188",
        "lasso b: 0.678",
        "median survival: 4",
        "log-rank p: 0.32",
        "cox hr: 0.233",
        "cox concordance: 0.833",
        "glm slope: 0.237",
        "survival rows: 10",
        "cox events: 8",
    ]


def test_arima_forecasting(tmp_path, monkeypatch):
    out = run_example("12_arima_forecasting.pea", tmp_path, monkeypatch)
    assert out == [
        "order: 1,1,0",
        "forecast: 31.82, 34.63",
        "selected: 2,1,0",
        "aic: -365.9",
        "auto forecast: 16, 26",
        "report forecast: 16, 26",
    ]
