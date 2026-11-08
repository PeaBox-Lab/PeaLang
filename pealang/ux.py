"""User-experience helpers: diagnostics, environment checks, and project scaffolding."""

from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path
from typing import Any

from .errors import PeaError


def doctor() -> dict[str, Any]:
    report = {
        "python": sys.version,
        "executable": sys.executable,
        "platform": sys.platform,
        "pealang": None,
    }
    try:
        from . import __version__
        report["pealang"] = __version__
    except Exception as exc:
        report["pealang_error"] = str(exc)
    optional = {}
    for module in ("cryptography", "fastapi", "numpy", "onnxruntime", "torch", "polars", "pyarrow"):
        try:
            m = __import__(module)
            optional[module] = getattr(m, "__version__", "available")
        except Exception:
            optional[module] = "missing"
    report["optional_dependencies"] = optional
    return report


def suggest(word: str, choices: list[str]) -> list[str]:
    return difflib.get_close_matches(str(word), [str(x) for x in choices], n=5, cutoff=0.6)


def explain_error(error: Any, choices: list[str] | None = None) -> str:
    text = str(error)
    suggestions = []
    lowered = text.lower()
    if "not found" in lowered:
        suggestions.append("Check the module path, file name, and current working directory.")
    if "permission" in lowered:
        suggestions.append("Grant the required capability through RuntimeOptions or --allow-process where appropriate.")
    if "syntax" in lowered or "expected" in lowered:
        suggestions.append("Run `pea fmt` and `pea check` to locate the syntax issue.")
    if choices:
        matches = suggest(text.split()[-1] if text.split() else text, choices)
        if matches:
            suggestions.append("Did you mean: " + ", ".join(matches))
    if not suggestions:
        suggestions.append("Run `pea check <file>` for a detailed diagnostic.")
    return text + "\nSuggestions:\n- " + "\n- ".join(suggestions)


def format_doctor(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, default=str)


def build_ux_namespace() -> dict[str, Any]:
    return {"doctor": doctor, "explain": explain_error, "suggest": suggest}
