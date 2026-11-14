"""Regression coverage for v137 developer experience."""

from pealang.devx import (
    build_devx_namespace,
    suggest_fix,
    explain_error_detailed,
    code_metrics,
    lint_source,
    format_source,
    dependency_check,
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


def test_build_devx_namespace():
    ns = build_devx_namespace()
    assert "suggest_fix" in ns
    assert "code_metrics" in ns
    assert "lint_source" in ns
    assert "format_source" in ns
    assert len(ns) == 7
