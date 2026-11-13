"""Regression coverage for v133 conformance and quality gates."""

from pealang.conformance_quality import (
    build_conformance_namespace,
    run_conformance_suite,
    check_api_stability,
    check_documentation_coverage,
    environment_check,
    generate_quality_report,
    hash_source_tree,
)


def test_run_conformance_suite():
    cases = [
        {"name": "add", "fn": lambda: 1 + 1, "expected": 2},
        {"name": "sub", "fn": lambda: 5 - 3, "expected": 2},
        {"name": "fail", "fn": lambda: 1 + 1, "expected": 3},
    ]
    result = run_conformance_suite(cases)
    assert result["total"] == 3
    assert result["passed"] == 2
    assert result["failed"] == 1
    assert result["pass_rate"] == 66.67


def test_check_api_stability():
    baseline = ["a", "b", "c"]
    current = ["a", "b", "c", "d"]
    result = check_api_stability(current, baseline)
    assert result["stable"] is True
    assert result["added"] == ["d"]
    assert result["removed"] == []


def test_check_api_stability_breaking():
    baseline = ["a", "b", "c"]
    current = ["a", "b"]
    result = check_api_stability(current, baseline)
    assert result["stable"] is False
    assert result["removed"] == ["c"]


def test_check_documentation_coverage():
    result = check_documentation_coverage(["a", "b", "c"], ["a", "b"])
    assert result["total"] == 3
    assert result["documented"] == 2
    assert result["undocumented"] == ["c"]
    assert result["coverage_pct"] == 66.67


def test_environment_check():
    result = environment_check()
    assert "python_version" in result
    assert result["python_ok"] is True
    assert "platform" in result


def test_generate_quality_report():
    report = generate_quality_report({"env": {"python": "3.12"}, "status": "ok"})
    assert "Quality Gate Report" in report
    assert "python" in report


def test_hash_source_tree():
    h = hash_source_tree(".")
    assert isinstance(h, str)
    assert len(h) == 64


def test_build_conformance_namespace():
    ns = build_conformance_namespace()
    assert "run_conformance_suite" in ns
    assert "check_api_stability" in ns
    assert "environment_check" in ns
    assert len(ns) == 6
