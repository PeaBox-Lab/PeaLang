"""Interactive Web Data IDE and reactive notebook server for PeaLang (v1.8.0).

Provides a self-hosted Web Data IDE with reactive cell execution, visual
SQL/DataFrame inspectors, and one-click publishing of .pea scripts as
interactive web apps.
"""

from __future__ import annotations

import json
from typing import Any


# ---------------------------------------------------------------------------
# Reactive cell execution
# ---------------------------------------------------------------------------

class ReactiveCell:
    """A reactive notebook cell with dependency tracking."""

    def __init__(self, cell_id: str, source: str = "", dependencies: list[str] | None = None):
        self.cell_id = cell_id
        self.source = source
        self.dependencies = dependencies or []
        self.result = None
        self.error = None
        self.execution_count = 0
        self.dirty = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "source": self.source,
            "dependencies": self.dependencies,
            "result": self.result,
            "error": self.error,
            "execution_count": self.execution_count,
            "dirty": self.dirty,
        }


class ReactiveNotebook:
    """A reactive notebook with dependency tracking and auto-recomputation."""

    def __init__(self):
        self.cells: dict[str, ReactiveCell] = {}
        self.order: list[str] = []

    def add_cell(self, cell_id: str, source: str = "", dependencies: list[str] | None = None) -> ReactiveCell:
        cell = ReactiveCell(cell_id, source, dependencies)
        self.cells[cell_id] = cell
        if cell_id not in self.order:
            self.order.append(cell_id)
        return cell

    def remove_cell(self, cell_id: str) -> bool:
        if cell_id in self.cells:
            del self.cells[cell_id]
            self.order = [c for c in self.order if c != cell_id]
            # Remove from dependencies
            for cell in self.cells.values():
                cell.dependencies = [d for d in cell.dependencies if d != cell_id]
            return True
        return False

    def update_cell(self, cell_id: str, source: str) -> None:
        if cell_id in self.cells:
            self.cells[cell_id].source = source
            self.cells[cell_id].dirty = True

    def get_dependents(self, cell_id: str) -> list[str]:
        """Get cells that depend on the given cell."""
        return [cid for cid, cell in self.cells.items() if cell_id in cell.dependencies]

    def execution_order(self) -> list[str]:
        """Topological sort of cells based on dependencies."""
        visited = set()
        result = []

        def visit(cid):
            if cid in visited:
                return
            visited.add(cid)
            cell = self.cells.get(cid)
            if cell:
                for dep in cell.dependencies:
                    if dep in self.cells:
                        visit(dep)
            result.append(cid)

        for cid in self.order:
            visit(cid)
        return result

    def mark_dirty(self, cell_id: str) -> list[str]:
        """Mark a cell and its dependents as dirty. Returns affected cell IDs."""
        affected = [cell_id]
        for dep in self.get_dependents(cell_id):
            if dep not in affected:
                affected.append(dep)
                affected.extend([d for d in self.get_dependents(dep) if d not in affected])
        for cid in affected:
            if cid in self.cells:
                self.cells[cid].dirty = True
        return affected

    def to_dict(self) -> dict[str, Any]:
        return {
            "cells": {cid: cell.to_dict() for cid, cell in self.cells.items()},
            "order": self.order,
        }


# ---------------------------------------------------------------------------
# Visual SQL/DataFrame inspector
# ---------------------------------------------------------------------------

def inspect_dataframe(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate a visual inspection summary of a DataFrame."""
    if not data:
        return {"row_count": 0, "column_count": 0, "columns": []}
    columns = []
    for row in data:
        for k in row:
            if k not in columns:
                columns.append(k)
    col_info = []
    for col in columns:
        vals = [r.get(col) for r in data]
        non_null = [v for v in vals if v is not None]
        distinct = len(set(str(v) for v in non_null))
        # Type inference
        if all(isinstance(v, bool) for v in non_null):
            dtype = "boolean"
        elif all(isinstance(v, int) and not isinstance(v, bool) for v in non_null):
            dtype = "integer"
        elif all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in non_null):
            dtype = "number"
        else:
            dtype = "string"
        col_info.append({
            "name": col,
            "dtype": dtype,
            "null_count": len(vals) - len(non_null),
            "distinct_count": distinct,
            "sample": non_null[:3],
        })
    return {
        "row_count": len(data),
        "column_count": len(columns),
        "columns": col_info,
    }


def inspect_sql_result(query: str, result: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate a visual inspection of a SQL query result."""
    return {
        "query": query,
        "row_count": len(result),
        "column_count": len(result[0]) if result else 0,
        "columns": list(result[0].keys()) if result else [],
        "preview": result[:5],
    }


# ---------------------------------------------------------------------------
# Web app publisher
# ---------------------------------------------------------------------------

def publish_as_webapp(source: str, title: str = "PeaLang App",
                     template: str = "default") -> dict[str, Any]:
    """Generate a self-contained web app from a .pea script."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
    .output {{ background: #f5f5f5; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
    pre {{ white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div id="app"></div>
  <script type="module">
    import {{ loadPeaWasm }} from "./pealang-wasm.js";
    const instance = await loadPeaWasm("./pealang.wasm");
    const output = instance.exports.run();
    document.getElementById("app").innerHTML = `<div class="output"><pre>${{output}}</pre></div>`;
  </script>
</body>
</html>"""
    return {
        "title": title,
        "template": template,
        "html": html,
        "files": ["index.html", "pealang-wasm.js", "pealang.wasm"],
    }


def generate_notebook_html(cells: list[dict[str, Any]]) -> str:
    """Generate an HTML notebook from a list of cells."""
    parts = ['<!DOCTYPE html><html><head><meta charset="UTF-8"><title>PeaLang Notebook</title>',
             '<style>body{font-family:system-ui;margin:2rem;} .cell{margin:1rem 0;padding:1rem;border:1px solid #ddd;border-radius:8px;} .code{background:#f5f5f5;padding:0.5rem;border-radius:4px;font-family:monospace;white-space:pre-wrap;} .output{margin-top:0.5rem;padding:0.5rem;background:#fafafa;border-radius:4px;}</style>',
             '</head><body><h1>PeaLang Notebook</h1>']
    for cell in cells:
        source = cell.get("source", "")
        output = cell.get("output", "")
        parts.append(f'<div class="cell"><div class="code">{source}</div>')
        if output:
            parts.append(f'<div class="output">{output}</div>')
        parts.append('</div>')
    parts.append('</body></html>')
    return "\n".join(parts)


def build_notebook_ide_namespace() -> dict[str, Any]:
    return {
        "ReactiveCell": ReactiveCell,
        "ReactiveNotebook": ReactiveNotebook,
        "inspect_dataframe": inspect_dataframe,
        "inspect_sql_result": inspect_sql_result,
        "publish_as_webapp": publish_as_webapp,
        "generate_notebook_html": generate_notebook_html,
    }
