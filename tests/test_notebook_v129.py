"""Regression coverage for v129 notebook-rich display hooks."""

from pealang.jupyter import RichResult
from pealang.notebook import (
    build_notebook_namespace,
    display_chart,
    display_evaluation,
    display_model,
    display_profile,
    display_records,
    display_report,
)


def test_display_records_basic():
    rows = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    r = display_records(rows)
    assert isinstance(r, RichResult)
    assert "text/html" in r.data
    assert "text/markdown" in r.data
    assert "application/json" in r.data
    assert r.data["application/json"]["row_count"] == 2


def test_display_records_title():
    rows = [{"a": 1}]
    r = display_records(rows, title="My Data")
    assert "My Data" in r.data["text/html"]
    assert "My Data" in r.data["text/markdown"]


def test_display_records_limit():
    rows = [{"a": i} for i in range(100)]
    r = display_records(rows, limit=5)
    assert r.data["application/json"]["row_count"] == 100
    assert len(r.data["application/json"]["rows"]) == 5


def test_display_profile():
    profile = {
        "fields": [
            {"name": "age", "type": "int", "count": 10, "missing": 1, "unique": 5, "mean": 30.0, "min": 20, "max": 40},
        ],
        "summary": {"rows": 10, "columns": 1},
    }
    r = display_profile(profile)
    assert isinstance(r, RichResult)
    assert "Data Profile" in r.data["text/html"]
    assert "Data Profile" in r.data["text/markdown"]


def test_display_model():
    model = {
        "estimator": "random_forest",
        "features": ["a", "b"],
        "metrics": {"accuracy": 0.9, "f1": 0.85},
        "params": {"n_trees": 10},
    }
    r = display_model(model)
    assert isinstance(r, RichResult)
    assert "random_forest" in r.data["text/html"]
    assert "accuracy" in r.data["text/html"]


def test_display_evaluation():
    ev = {
        "accuracy": 0.95,
        "metrics": {"precision": 0.9, "recall": 0.88},
        "confusion_matrix": [[5, 1], [2, 8]],
    }
    r = display_evaluation(ev)
    assert isinstance(r, RichResult)
    assert "0.95" in r.data["text/html"]
    assert "Confusion Matrix" in r.data["text/html"]


def test_display_chart():
    chart = {"kind": "bar", "title": "Sales", "data": [{"x": "a", "y": 10}, {"x": "b", "y": 20}]}
    r = display_chart(chart)
    assert isinstance(r, RichResult)
    assert "Sales" in r.data["text/html"]
    assert "bar" in r.data["text/plain"].lower() or "Bar" in r.data["text/html"]


def test_display_report_string():
    r = display_report("# Hello\n\nThis is a report.")
    assert isinstance(r, RichResult)
    assert "Hello" in r.data["text/markdown"]


def test_display_report_dict():
    r = display_report({"kind": "profile", "content": "Profile report content"})
    assert isinstance(r, RichResult)
    assert "Profile report content" in r.data["text/markdown"]


def test_build_notebook_namespace():
    ns = build_notebook_namespace()
    assert "display_records" in ns
    assert "display_profile" in ns
    assert "display_model" in ns
    assert "display_evaluation" in ns
    assert "display_chart" in ns
    assert "display_report" in ns
    assert len(ns) == 6


def test_display_records_dataframe_like():
    class FakeDF:
        def to_dicts(self):
            return [{"x": 1}, {"x": 2}]
    r = display_records(FakeDF())
    assert r.data["application/json"]["row_count"] == 2
