"""Regression coverage for v137 developer experience."""

from pealang.devx import (
    build_devx_namespace,
    suggest_fix,
    explain_error_detailed,
    code_metrics,
    lint_source,
    format_source,
    dependency_check,
    diagnose_source,
    cheatsheet,
    project_check,
)


def test_suggest_fix():
    suggestions = suggest_fix("Variable 'x' not defined")
    assert len(suggestions) > 0
    assert any("spelling" in s.lower() or "undeclared" in s.lower() for s in suggestions)


def test_explain_error_detailed():
    result = explain_error_detailed("Syntax error at 5:10", line=5)
    assert "suggestions" in result
    assert result["line"] == 5


def test_code_metrics():
    src = "let x = 1\n// comment\n\nfunction f() { return x }\n"
    metrics = code_metrics(src)
    assert metrics["total_lines"] == 4
    assert metrics["code_lines"] == 2
    assert metrics["comment_lines"] == 1
    assert metrics["blank_lines"] == 1
    assert metrics["function_count"] == 1
    assert metrics["variable_count"] == 1


def test_lint_source():
    src = "let x = 1   \nlet y = 2\n"
    issues = lint_source(src)
    assert any("Trailing whitespace" in i["message"] for i in issues)


def test_format_source():
    src = "function f() {\nlet x = 1\nreturn x\n}"
    formatted = format_source(src)
    assert "    let x = 1" in formatted


def test_dependency_check_missing():
    result = dependency_check("nonexistent.json")
    assert "error" in result


def test_diagnose_source():
    clean = diagnose_source("let x: Int = 5\nprint x")
    assert clean["ok"] is True
    assert clean["health"] == 100

    broken = diagnose_source('let x: Int = "hi"\nprint x')
    assert broken["ok"] is False
    assert broken["counts"]["error"] == 1
    assert broken["diagnostics"][0]["origin"] == "type"


def test_diagnose_source_includes_lint():
    src = "let x = 1   \n"  # trailing whitespace
    r = diagnose_source(src)
    assert any(d["origin"] == "lint" for d in r["diagnostics"])


def test_cheatsheet():
    cs = cheatsheet()
    assert "overview" not in cs  # returns the default overview dict
    assert cs["title"].lower().startswith("pealang")
    assert isinstance(cs["commands"], list)

    t = cheatsheet("types")
    assert t["title"] == "Types"
    assert isinstance(t["syntax"], list)

    bogus = cheatsheet("bogus")
    assert "error" in bogus
    assert "available" in bogus


def test_project_check_basic(tmp_path):
    (tmp_path / "good.pea").write_text("let x: Int = 5\nprint x\n", encoding="utf-8")
    (tmp_path / "bad.pea").write_text('let x: Int = "nope"\nprint x\n', encoding="utf-8")
    from pealang.devx import project_check
    out = project_check(str(tmp_path))
    assert out["totals"]["files"] == 2
    assert out["totals"]["errors"] == 1
    assert out["totals"]["ok"] is False
    names = [f["file"] for f in out["files"]]
    assert any("bad.pea" in n for n in names)


def test_project_check_all_ok(tmp_path):
    (tmp_path / "ok.pea").write_text("let x: Int = 5\nprint x\n", encoding="utf-8")
    from pealang.devx import project_check
    out = project_check(str(tmp_path))
    assert out["totals"]["ok"] is True
    assert out["totals"]["errors"] == 0


def test_build_devx_namespace():
    ns = build_devx_namespace()
    assert "suggest_fix" in ns
    assert "code_metrics" in ns
    assert "lint_source" in ns
    assert "format_source" in ns
    assert "diagnose_source" in ns
    assert "cheatsheet" in ns
    assert "project_check" in ns
    assert len(ns) == 10
