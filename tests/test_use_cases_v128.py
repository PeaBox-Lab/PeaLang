from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def test_reporting_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "24_reporting.pea"
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    assert out == [
        "Profile markdown written to reports/profile_report.md",
        "Profile HTML written to reports/profile_report.html",
        "Model markdown written to reports/model_report.md",
        "Model HTML written to reports/model_report.html",
        "Evaluation markdown written to reports/evaluation_report.md",
        "Evaluation HTML written to reports/evaluation_report.html",
        "JSON written to reports/evaluation_report.json",
    ]
    report = (tmp_path / "reports" / "model_report.md").read_text(encoding="utf-8")
    assert report.startswith("# Model Summary")
    evaluation = (tmp_path / "reports" / "evaluation_report.md").read_text(encoding="utf-8")
    assert evaluation.startswith("# Evaluation Report")
