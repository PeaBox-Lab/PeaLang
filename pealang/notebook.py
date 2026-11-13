"""Notebook-rich display hooks for Jupyter and other interactive environments.

This module extends the basic :class:`pealang.jupyter.RichDisplay` helpers with
rich, dependency-free renderers for the data-science objects produced by
PeaLang's ``analysis``, ``stats`` and reporting APIs.  Every renderer returns a
:class:`pealang.jupyter.RichResult` carrying multiple MIME bundles so that
notebooks can pick the best representation automatically.

Supported rich representations
------------------------------
* ``text/plain``   - compact textual summary
* ``text/html``     - styled HTML table / card
* ``text/markdown`` - Markdown table / summary
* ``application/json`` - structured payload for programmatic use

The helpers are pure Python and require no external dependencies.
"""

from __future__ import annotations

from html import escape
from typing import Any

from .jupyter import RichResult


def _is_record_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(x, dict) for x in value)


def _columns(rows: list[dict]) -> list[str]:
    seen: list[str] = []
    for row in rows:
        for key in row:
            if key not in seen:
                seen.append(key)
    return seen


def _html_table(columns: list[str], rows: list[dict], *, limit: int = 50) -> str:
    head = "".join(f"<th>{escape(str(c))}</th>" for c in columns)
    body_parts = []
    for row in rows[:limit]:
        cells = "".join(f"<td>{escape(str(row.get(c, '')))}</td>" for c in columns)
        body_parts.append(f"<tr>{cells}</tr>")
    body = "".join(body_parts)
    extra = ""
    if len(rows) > limit:
        extra = f"<p><em>... {len(rows) - limit} more rows</em></p>"
    return (
        f'<table class="pealang-notebook"><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table>{extra}"
    )


def _markdown_table(columns: list[str], rows: list[dict], *, limit: int = 50) -> str:
    if not columns:
        return ""
    header = "| " + " | ".join(str(c) for c in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for row in rows[:limit]:
        cells = " | ".join(str(row.get(c, "")) for c in columns)
        lines.append(f"| {cells} |")
    if len(rows) > limit:
        lines.append(f"| ... | {len(rows) - limit} more rows |")
    return "\n".join(lines)


def display_records(rows: Any, title: str | None = None, limit: int = 50) -> RichResult:
    """Rich display for a list of record dicts (or a DataFrame-like object)."""
    if hasattr(rows, "to_dicts"):
        rows = rows.to_dicts()
    if not _is_record_list(rows):
        rows = [rows] if isinstance(rows, dict) else list(rows or [])
    columns = _columns(rows)
    html = _html_table(columns, rows, limit=limit)
    md = _markdown_table(columns, rows, limit=limit)
    if title:
        html = f"<h3>{escape(str(title))}</h3>" + html
        md = f"### {title}\n\n" + md
    text = f"{len(rows)} rows x {len(columns)} columns"
    return RichResult(
        {
            "text/plain": text,
            "text/html": html,
            "text/markdown": md,
            "application/json": {"columns": columns, "rows": rows[:limit], "row_count": len(rows)},
        },
        {},
    )


def display_profile(profile: Any) -> RichResult:
    """Rich display for a data profile record (fields + summary)."""
    if isinstance(profile, dict):
        fields = profile.get("fields", [])
        summary = profile.get("summary", {})
    else:
        fields = getattr(profile, "fields", [])
        summary = getattr(profile, "summary", {})
    if not isinstance(fields, list):
        fields = []
    columns = ["field", "type", "count", "missing", "unique", "mean", "min", "max"]
    rows = []
    for f in fields:
        if isinstance(f, dict):
            rows.append({
                "field": f.get("name", f.get("field", "")),
                "type": f.get("type", ""),
                "count": f.get("count", ""),
                "missing": f.get("missing", f.get("null_count", "")),
                "unique": f.get("unique", f.get("nunique", "")),
                "mean": f.get("mean", ""),
                "min": f.get("min", ""),
                "max": f.get("max", ""),
            })
    html = _html_table(columns, rows)
    md = _markdown_table(columns, rows)
    summary_html = ""
    summary_md = ""
    if summary:
        items = "".join(f"<li><b>{escape(str(k))}</b>: {escape(str(v))}</li>" for k, v in summary.items())
        summary_html = f"<ul>{items}</ul>"
        summary_md = "\n".join(f"- **{k}**: {v}" for k, v in summary.items())
    html = f"<h3>Data Profile</h3>{summary_html}{html}"
    md = f"### Data Profile\n\n{summary_md}\n\n{md}" if summary_md else f"### Data Profile\n\n{md}"
    text = f"Profile: {len(rows)} fields"
    return RichResult(
        {
            "text/plain": text,
            "text/html": html,
            "text/markdown": md,
            "application/json": {"fields": rows, "summary": summary},
        },
        {},
    )


def display_model(model: Any) -> RichResult:
    """Rich display for a fitted model / estimator record."""
    if isinstance(model, dict):
        estimator = model.get("estimator", model.get("kind", "model"))
        metrics = model.get("metrics", {})
        features = model.get("features", [])
        params = model.get("params", {})
    else:
        estimator = getattr(model, "estimator", getattr(model, "kind", "model"))
        metrics = getattr(model, "metrics", {})
        features = getattr(model, "features", [])
        params = getattr(model, "params", {})
    html = f"<h3>Model: {escape(str(estimator))}</h3>"
    md = f"### Model: {estimator}\n"
    if features:
        html += f"<p><b>Features:</b> {escape(', '.join(str(f) for f in features))}</p>"
        md += f"\n**Features:** {', '.join(str(f) for f in features)}\n"
    if metrics:
        mcols = ["metric", "value"]
        mrows = [{"metric": k, "value": v} for k, v in metrics.items()]
        html += _html_table(mcols, mrows)
        md += "\n" + _markdown_table(mcols, mrows) + "\n"
    if params:
        html += "<h4>Parameters</h4><ul>" + "".join(
            f"<li><b>{escape(str(k))}</b>: {escape(str(v))}</li>" for k, v in params.items()
        ) + "</ul>"
        md += "\n**Parameters:**\n" + "\n".join(f"- **{k}**: {v}" for k, v in params.items()) + "\n"
    text = f"Model: {estimator} ({len(features)} features, {len(metrics)} metrics)"
    return RichResult(
        {
            "text/plain": text,
            "text/html": html,
            "text/markdown": md,
            "application/json": {"estimator": estimator, "features": features, "metrics": metrics, "params": params},
        },
        {},
    )


def display_evaluation(evaluation: Any) -> RichResult:
    """Rich display for an evaluation result record."""
    if isinstance(evaluation, dict):
        accuracy = evaluation.get("accuracy")
        metrics = evaluation.get("metrics", {})
        confusion = evaluation.get("confusion_matrix")
        report = evaluation.get("report", {})
    else:
        accuracy = getattr(evaluation, "accuracy", None)
        metrics = getattr(evaluation, "metrics", {})
        confusion = getattr(evaluation, "confusion_matrix", None)
        report = getattr(evaluation, "report", {})
    html = "<h3>Evaluation</h3>"
    md = "### Evaluation\n"
    if accuracy is not None:
        html += f"<p><b>Accuracy:</b> {escape(str(accuracy))}</p>"
        md += f"\n**Accuracy:** {accuracy}\n"
    if metrics:
        mcols = ["metric", "value"]
        mrows = [{"metric": k, "value": v} for k, v in metrics.items()]
        html += _html_table(mcols, mrows)
        md += "\n" + _markdown_table(mcols, mrows) + "\n"
    if confusion is not None:
        html += "<h4>Confusion Matrix</h4>"
        md += "\n**Confusion Matrix:**\n"
        if isinstance(confusion, list) and confusion and isinstance(confusion[0], list):
            ncols = len(confusion[0])
            cols = [str(i) for i in range(ncols)]
            cm_rows = [dict(enumerate(row)) for row in confusion]
            # Convert to string-keyed dicts
            cm_rows = [{str(i): row[i] for i in range(len(row))} for row in confusion]
            html += _html_table(cols, cm_rows)
            md += _markdown_table(cols, cm_rows)
    text = f"Evaluation: accuracy={accuracy}" if accuracy is not None else "Evaluation"
    return RichResult(
        {
            "text/plain": text,
            "text/html": html,
            "text/markdown": md,
            "application/json": {"accuracy": accuracy, "metrics": metrics, "confusion_matrix": confusion, "report": report},
        },
        {},
    )


def display_chart(chart: Any) -> RichResult:
    """Rich display for a chart specification dict."""
    if isinstance(chart, dict):
        kind = chart.get("kind", chart.get("type", "chart"))
        title = chart.get("title", "")
        data = chart.get("data", chart.get("values", []))
    else:
        kind = getattr(chart, "kind", getattr(chart, "type", "chart"))
        title = getattr(chart, "title", "")
        data = getattr(chart, "data", getattr(chart, "values", []))
    html = f"<h3>{escape(str(title or kind.title() + ' Chart'))}</h3>"
    md = f"### {title or kind.title() + ' Chart'}\n"
    if isinstance(data, list) and data and isinstance(data[0], dict):
        cols = _columns(data)
        html += _html_table(cols, data)
        md += "\n" + _markdown_table(cols, data) + "\n"
    elif isinstance(data, list):
        html += "<ul>" + "".join(f"<li>{escape(str(v))}</li>" for v in data) + "</ul>"
        md += "\n" + "\n".join(f"- {v}" for v in data) + "\n"
    text = f"Chart: {kind} ({len(data) if isinstance(data, list) else 0} points)"
    return RichResult(
        {
            "text/plain": text,
            "text/html": html,
            "text/markdown": md,
            "application/json": {"kind": kind, "title": title, "data": data},
        },
        {},
    )


def display_report(report: Any) -> RichResult:
    """Rich display for a report dict or markdown/html string."""
    if isinstance(report, str):
        content = report
        kind = "markdown"
    elif isinstance(report, dict):
        content = report.get("content", report.get("markdown", report.get("html", "")))
        kind = report.get("kind", "report")
    else:
        content = str(report)
        kind = "report"
    html = f"<div class='pealang-report'>{escape(str(content))}</div>" if kind != "html" else str(content)
    md = str(content)
    text = f"Report ({kind}): {len(str(content))} chars"
    return RichResult(
        {
            "text/plain": text,
            "text/html": html,
            "text/markdown": md,
            "application/json": {"kind": kind, "content": content},
        },
        {},
    )


def build_notebook_namespace() -> dict[str, Any]:
    return {
        "display_records": display_records,
        "display_profile": display_profile,
        "display_model": display_model,
        "display_evaluation": display_evaluation,
        "display_chart": display_chart,
        "display_report": display_report,
    }
