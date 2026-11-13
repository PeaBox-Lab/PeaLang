"""Conformance and quality-gate helpers for PeaLang.

Provides tools for running conformance checks, validating API stability,
and generating quality-gate reports.  Supports the final 1.0 release
certification process.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Iterable


def run_conformance_suite(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Run a list of conformance cases and return a summary.

    Each case: {"name": str, "fn": callable, "expected": Any}
    """
    results = []
    passed = 0
    failed = 0
    for case in cases or []:
        name = case.get("name", "unnamed")
        fn = case.get("fn")
        expected = case.get("expected")
        try:
            actual = fn() if callable(fn) else None
            ok = actual == expected
            if ok:
                passed += 1
            else:
                failed += 1
            results.append({"name": name, "passed": ok, "expected": expected, "actual": actual})
        except Exception as exc:
            failed += 1
            results.append({"name": name, "passed": False, "error": str(exc)})
    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(results) * 100, 2) if results else 0.0,
        "results": results,
    }


def check_api_stability(current: list[str], baseline: list[str]) -> dict[str, Any]:
    """Compare current API surface against a baseline. Returns added/removed/changed."""
    current_set = set(current or [])
    baseline_set = set(baseline or [])
    added = sorted(current_set - baseline_set)
    removed = sorted(baseline_set - current_set)
    return {
        "stable": len(removed) == 0,
        "added": added,
        "removed": removed,
        "current_count": len(current_set),
        "baseline_count": len(baseline_set),
    }


def check_documentation_coverage(modules: list[str], documented: list[str]) -> dict[str, Any]:
    """Check that all modules have documentation."""
    mod_set = set(modules or [])
    doc_set = set(documented or [])
    undocumented = sorted(mod_set - doc_set)
    return {
        "total": len(mod_set),
        "documented": len(mod_set & doc_set),
        "undocumented": undocumented,
        "coverage_pct": round(len(mod_set & doc_set) / len(mod_set) * 100, 2) if mod_set else 0.0,
    }


def environment_check() -> dict[str, Any]:
    """Check the runtime environment for required capabilities."""
    checks = {}
    # Python version
    checks["python_version"] = sys.version.split()[0]
    checks["python_ok"] = sys.version_info >= (3, 10)
    # Optional modules
    for mod in ("json", "csv", "sqlite3", "hashlib", "pathlib", "zipfile", "xml"):
        try:
            __import__(mod)
            checks[f"stdlib_{mod}"] = "ok"
        except Exception:
            checks[f"stdlib_{mod}"] = "missing"
    # Platform
    checks["platform"] = sys.platform
    checks["cwd"] = os.getcwd()
    return checks


def generate_quality_report(checks: dict[str, Any]) -> str:
    """Generate a markdown quality-gate report from check results."""
    lines = ["# Quality Gate Report", ""]
    for key, value in (checks or {}).items():
        if isinstance(value, dict):
            lines.append(f"## {key}")
            for k, v in value.items():
                lines.append(f"- **{k}**: {v}")
            lines.append("")
        else:
            lines.append(f"- **{key}**: {value}")
    lines.append("")
    return "\n".join(lines)


def hash_source_tree(root: str = ".") -> str:
    """Compute a deterministic hash of all Python source files."""
    h = hashlib.sha256()
    files = sorted(Path(root).rglob("*.py"))
    for f in files:
        if "__pycache__" in str(f):
            continue
        h.update(str(f.relative_to(root)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def build_conformance_namespace() -> dict[str, Any]:
    return {
        "run_conformance_suite": run_conformance_suite,
        "check_api_stability": check_api_stability,
        "check_documentation_coverage": check_documentation_coverage,
        "environment_check": environment_check,
        "generate_quality_report": generate_quality_report,
        "hash_source_tree": hash_source_tree,
    }
