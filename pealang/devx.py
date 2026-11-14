"""Developer experience and tooling enhancements for PeaLang.

Provides improved error suggestions, project scaffolding, code formatting
hints, and developer diagnostics for a better coding experience.
"""

from __future__ import annotations

import difflib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def suggest_fix(error_msg: str, source: str = "") -> list[str]:
    """Suggest fixes for a given error message."""
    suggestions = []
    lowered = error_msg.lower()
    if "not defined" in lowered or "not found" in lowered:
        suggestions.append("Check spelling and ensure the variable/function is declared before use.")
        suggestions.append("Use 'pea check' to find undeclared identifiers.")
    if "type" in lowered and "mismatch" in lowered:
        suggestions.append("Ensure the value matches the declared type.")
        suggestions.append("Use type coercion: int(), float(), str(), bool().")
    if "syntax" in lowered or "unexpected" in lowered:
        suggestions.append("Check for missing brackets, quotes, or semicolons.")
        suggestions.append("Run 'pea fmt' to auto-format the source.")
    if "index" in lowered or "out of range" in lowered:
        suggestions.append("Verify list/dict indices are within bounds.")
        suggestions.append("Use safe access: get(list, index, default).")
    if "permission" in lowered or "not allowed" in lowered:
        suggestions.append("Grant required capabilities via RuntimeOptions or --allow-process.")
    if "import" in lowered or "module" in lowered:
        suggestions.append("Check module path and ensure dependencies are installed.")
    if not suggestions:
        suggestions.append("Run 'pea check <file>' for detailed diagnostics.")
    return suggestions


def explain_error_detailed(error: Any, source: str = "", line: int = 0) -> dict[str, Any]:
    """Provide a detailed error explanation with context."""
    msg = str(error)
    result = {
        "error": msg,
        "suggestions": suggest_fix(msg, source),
        "line": line,
    }
    # Try to extract line from error message
    import re as _re
    m = _re.search(r":(\d+):(\d+)", msg)
    if m:
        result["line"] = int(m.group(1))
        result["column"] = int(m.group(2))
    # Extract context lines
    if source and result["line"] > 0:
        lines = source.splitlines()
        ln = result["line"]
        start = max(0, ln - 3)
        end = min(len(lines), ln + 2)
        result["context"] = [
            {"line": i + 1, "text": lines[i], "highlight": i + 1 == ln}
            for i in range(start, end)
        ]
    return result


def project_scaffold(name: str, template: str = "default", target_dir: str = ".") -> dict[str, Any]:
    """Scaffold a new project with best-practice structure."""
    from .project import init_project
    manifest_path = init_project(target_dir, name=name, template=template)
    root = Path(manifest_path).parent
    # Create additional structure
    (root / "tests").mkdir(exist_ok=True)
    (root / "docs").mkdir(exist_ok=True)
    (root / "modules").mkdir(exist_ok=True)
    # Write a README
    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(f"# {name}\n\nA PeaLang project.\n", encoding="utf-8")
    # Write a .gitignore
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("__pycache__/\n*.pyc\n.venv/\nreports/\n", encoding="utf-8")
    return {"root": str(root), "manifest": manifest_path, "template": template}


def code_metrics(source: str) -> dict[str, Any]:
    """Compute basic code metrics for a PeaLang source file."""
    lines = source.splitlines()
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith("//")]
    comment_lines = [l for l in lines if l.strip().startswith("//")]
    blank_lines = [l for l in lines if not l.strip()]
    # Count functions
    func_count = len(re.findall(r'\bfunction\b', source))
    # Count variables
    var_count = len(re.findall(r'\blet\b|\bconst\b', source))
    return {
        "total_lines": len(lines),
        "code_lines": len(code_lines),
        "comment_lines": len(comment_lines),
        "blank_lines": len(blank_lines),
        "function_count": func_count,
        "variable_count": var_count,
        "comment_ratio": round(len(comment_lines) / len(lines) * 100, 2) if lines else 0.0,
    }


def lint_source(source: str) -> list[dict[str, Any]]:
    """Basic linting for PeaLang source."""
    issues = []
    lines = source.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Check for trailing whitespace
        if line != line.rstrip():
            issues.append({"line": i, "severity": "info", "message": "Trailing whitespace"})
        # Check for long lines
        if len(line) > 120:
            issues.append({"line": i, "severity": "warning", "message": f"Line too long ({len(line)} > 120)"})
        # Check for TODO/FIXME
        if "TODO" in line or "FIXME" in line:
            issues.append({"line": i, "severity": "info", "message": "TODO/FIXME found"})
        # Check for console.log or debug
        if "print " in stripped and "debug" in stripped.lower():
            issues.append({"line": i, "severity": "warning", "message": "Debug print statement"})
    return issues


def format_source(source: str) -> str:
    """Basic source formatting (indentation normalization)."""
    lines = source.splitlines()
    result = []
    indent = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append("")
            continue
        # Decrease indent for closing braces
        if stripped.startswith("}"):
            indent = max(0, indent - 1)
        result.append("    " * indent + stripped)
        # Increase indent for opening braces
        if stripped.endswith("{") or stripped.endswith("{ "):
            indent += 1
    return "\n".join(result) + "\n"


def dependency_check(manifest_path: str = "pea.json") -> dict[str, Any]:
    """Check project dependencies for issues."""
    path = Path(manifest_path)
    if not path.exists():
        return {"error": "No pea.json found"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": f"Invalid JSON: {exc}"}
    deps = data.get("dependencies", {})
    issues = []
    for name, spec in deps.items():
        if not isinstance(spec, dict):
            issues.append({"dependency": name, "issue": "Invalid spec format"})
            continue
        dep_path = spec.get("path")
        if dep_path and not Path(dep_path).exists():
            issues.append({"dependency": name, "issue": f"Path not found: {dep_path}"})
    return {"dependencies": len(deps), "issues": issues, "ok": len(issues) == 0}


def build_devx_namespace() -> dict[str, Any]:
    return {
        "suggest_fix": suggest_fix,
        "explain_error_detailed": explain_error_detailed,
        "project_scaffold": project_scaffold,
        "code_metrics": code_metrics,
        "lint_source": lint_source,
        "format_source": format_source,
        "dependency_check": dependency_check,
    }
