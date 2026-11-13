from pathlib import Path

from pealang import analysis, execute

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def test_profile_markdown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = [
        {"category": "A", "value": 10},
        {"category": "B", "value": 20},
        {"category": "A", "value": 30},
    ]
    md = analysis.profile_markdown(data)
    assert "# Data Profile" in md
    assert "Rows: 3" in md
    assert "Columns: 2" in md
    assert "| Field | Type | Missing | Distinct |" in md


def test_profile_html_contains_markdown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = [{"category": "A", "value": 10}]
    html = analysis.profile_html(data)
    assert "<!doctype html>" in html
    assert "<h1>PeaLang Report</h1>" in html
    # Markdown is rendered inline, not JSON dumped
    assert "# Data Profile" in html
    assert "Rows: 1" in html
    # Angle brackets escaped in markdown content
    assert "&lt;script&gt;" not in html


def test_report_markdown_autodetect_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = [{"x": 1, "y": 2}]
    md = analysis.report_markdown(data)
    assert "# Data Profile" in md


def test_report_markdown_autodetect_model(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    model = {"estimator": "forest", "task": "classification", "n_rows": 10, "n_features": 3}
    md = analysis.report_markdown(model)
    assert "# Model Summary" in md
    assert "Estimator: forest" in md


def test_report_markdown_autodetect_evaluation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    evaluation = {"accuracy": 0.88, "f1": 0.80}
    md = analysis.report_markdown(evaluation)
    assert "# Evaluation Report" in md
    assert "accuracy" in md


def test_model_report_markdown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    model = {
        "estimator": "random_forest",
        "task": "classification",
        "n_rows": 100,
        "n_features": 5,
        "output_features": ["score", "probability"],
        "importance": [{"feature": "value", "importance": 0.45}],
        "train_accuracy": 0.85,
        "train_r2": 0.72,
        "classes": ["low", "high"],
    }
    md = analysis.model_markdown(model)
    assert md.startswith("# Model Summary")
    assert "Estimator: random_forest" in md
    assert "Feature Importance:" in md
    assert "| value | 0.4500 |" in md


def test_model_report_html(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    model = {"estimator": "forest", "task": "classification", "n_rows": 10, "n_features": 3}
    html = analysis.model_html(model)
    assert "# Model Summary" in html
    assert "<h1>Model Summary</h1>" in html


def test_evaluation_report_markdown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    evaluation = {"accuracy": 0.88, "precision": 0.82, "f1": 0.80}
    md = analysis.evaluation_markdown(evaluation)
    assert "# Evaluation Report" in md
    assert "accuracy" in md


def test_evaluation_report_html_escapes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    evaluation = {"accuracy": 0.88}
    html = analysis.evaluation_html(evaluation)
    assert "# Evaluation Report" in html
    # No raw angle-bracket injection from markdown text
    assert "<script>" not in html


def test_write_report_markdown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = [{"category": "A", "value": 10}]
    target = tmp_path / "reports" / "profile_report.md"
    analysis.write_report_markdown(str(target), data)
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "# Data Profile" in content
    assert "Rows: 1" in content


def test_write_report_html(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = [{"category": "A", "value": 10}]
    target = tmp_path / "reports" / "profile_report.html"
    analysis.write_report_html(str(target), data)
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "# Data Profile" in content


def test_write_report_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    evaluation = {"accuracy": 0.88}
    target = tmp_path / "reports" / "evaluation_report.json"
    analysis.write_report_json(str(target), evaluation)
    assert target.exists()
    import json as _json
    parsed = _json.loads(target.read_text(encoding="utf-8"))
    assert parsed["accuracy"] == 0.88


def test_write_report_model_kind(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    model = {"estimator": "forest", "task": "classification", "n_rows": 10, "n_features": 3}
    target = tmp_path / "reports" / "model_report.md"
    analysis.write_report_markdown(str(target), model)
    content = target.read_text(encoding="utf-8")
    assert "# Model Summary" in content


def test_write_report_evaluation_kind(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    evaluation = {"accuracy": 0.88}
    target = tmp_path / "reports" / "evaluation_report.md"
    analysis.write_report_markdown(str(target), evaluation)
    content = target.read_text(encoding="utf-8")
    assert "# Evaluation Report" in content


def test_example_reporting_writes_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    name = "24_reporting.pea"
    source = (EXAMPLES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(EXAMPLES / name))
    assert (tmp_path / "reports" / "profile_report.md").exists()
    assert (tmp_path / "reports" / "profile_report.html").exists()
    assert (tmp_path / "reports" / "model_report.md").exists()
    assert (tmp_path / "reports" / "model_report.html").exists()
    assert (tmp_path / "reports" / "evaluation_report.md").exists()
    assert (tmp_path / "reports" / "evaluation_report.html").exists()
    assert (tmp_path / "reports" / "evaluation_report.json").exists()
    assert (tmp_path / "reports" / "model_report.md").exists()
    # Model report content must not be a plain profile
    content = (tmp_path / "reports" / "model_report.md").read_text(encoding="utf-8")
    assert "# Model Summary" in content
    # Profile report content must be a profile
    pcontent = (tmp_path / "reports" / "profile_report.md").read_text(encoding="utf-8")
    assert "# Data Profile" in pcontent
    # Evaluation report content must be evaluation
    econtent = (tmp_path / "reports" / "evaluation_report.md").read_text(encoding="utf-8")
    assert "# Evaluation Report" in econtent


def test_report_html_escape_angle_brackets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    model = {"estimator": "x", "task": "classification", "n_rows": 10, "n_features": 3, "output_features": ["<script>"]}
    html = analysis.report_html(model)
    assert "# Model Summary" in html
    # No raw angle-bracket injection; escaped as HTML entities
    assert "<script>" not in html
    assert "&lt;script&gt;" in html