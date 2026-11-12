from pathlib import Path

from pealang import execute

CASES = Path(__file__).resolve().parent.parent / "examples" / "use_cases"


def run_example(name, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = (CASES / name).read_text(encoding="utf-8")
    out = []
    execute(source, output=out.append, source_name=str(CASES / name))
    return out


def test_sales_pipeline(tmp_path, monkeypatch):
    out = run_example("01_sales_pipeline.pea", tmp_path, monkeypatch)
    assert out[0] == "clean rows: 4"
    assert out[1] == "total revenue: 157"
    assert out[2] == "regions: 2"
    assert out[3] == "top region: North"
    assert (tmp_path / "out" / "sales_report.json").exists()


def test_analytics_report(tmp_path, monkeypatch):
    out = run_example("02_analytics_report.pea", tmp_path, monkeypatch)
    assert out[0] == "rows: 5"
    assert out[1] == "columns: 3"
    assert out[2] == "score mean: 86.4"
    assert out[3] == "score correlates with hours: true"
    assert out[5] == "roundtrip rows: 5"
    assert out[6] == "has profile heading: true"


def test_sql_analytics(tmp_path, monkeypatch):
    out = run_example("03_sql_analytics.pea", tmp_path, monkeypatch)
    assert out[0] == "total: 750"
    assert out[1] == "months: 2"
    assert out[2] == "jan revenue: 320"
    assert out[3] == "top customer: c2"
    assert out[4] == "ranked rows: 5"


def test_polyglot_bridge(tmp_path, monkeypatch):
    out = run_example("04_polyglot_bridge.pea", tmp_path, monkeypatch)
    assert out[0] == "python sqrt: 13"
    assert out[1] == "has host system: true"
    assert out[2] == "go has package: true"
    assert out[3] == "go has invoke: true"
    assert out[4] == "ts has invoke: true"
    assert out[5] in ("go available: true", "go available: false")


def test_web_data_api(tmp_path, monkeypatch):
    out = run_example("05_web_data_api.pea", tmp_path, monkeypatch)
    assert out == ["200", "200", "summary has groups: true"]


def test_data_and_polyglot_templates():
    from pealang.project import TEMPLATES

    assert "data" in TEMPLATES and "polyglot" in TEMPLATES
    assert "analysis.sql" in TEMPLATES["data"]
    assert "interop.generate_go" in TEMPLATES["polyglot"]
