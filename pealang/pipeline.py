"""Feature engineering pipelines: impute, encode and scale in order.

This module composes preprocessing steps into a fitted transformer that can be
reapplied to new rows. It is pure Python and dependency-free, and fills the gap
between raw records and the numeric matrices expected by
:mod:`pealang.trees` and :mod:`pealang.boosting`.

Steps are plain records, so they work naturally in PeaLang::

    let steps = [
        {"op": "impute", "method": "auto"},
        {"op": "encode", "method": "onehot"},
        {"op": "scale", "method": "standard"}
    ]

A pipeline is fitted once with :func:`fit_pipeline`; the returned transformer
stores every learned fill value, category level, mean and scale, and
:func:`transform_pipeline` reapplies them to new data.
"""

from __future__ import annotations

import math
from typing import Any, Iterable

from .trees import _classes


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _missing(value: Any) -> bool:
    return value is None or (
        isinstance(value, float) and math.isnan(value)
    )


def _rows(features: Any) -> list[list[Any]]:
    rows = [list(row) for row in (features or [])]
    if not rows:
        raise ValueError("features are required")
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise ValueError("feature rows must be non-empty and equal length")
    return rows


def _names(names: Any, width: int) -> list[str]:
    if names is None:
        return ["x" + str(index + 1) for index in range(width)]
    labels = [str(name) for name in names]
    if len(labels) != width:
        raise ValueError("feature names must match the number of features")
    return labels


def _numeric_column(values: list[Any]) -> bool:
    seen = False
    for value in values:
        if _missing(value):
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        seen = True
    return seen


def _numeric(value: Any, message: str) -> float:
    if isinstance(value, bool):
        raise ValueError(message)
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(message) from None
    if math.isnan(number):
        raise ValueError(message)
    return number


def _numeric_rows(rows: list[list[Any]]) -> list[list[float]]:
    message = (
        "pipeline output must be numeric; add an impute step for missing "
        "values and an encode step for categorical columns"
    )
    return [[_numeric(value, message) for value in row] for row in rows]


def _label(level: Any) -> str:
    if level is None:
        return "null"
    return str(level)


def _fit_impute(step: dict[str, Any], rows: list[list[Any]],
                names: list[str]) -> tuple[dict[str, Any], list[list[Any]]]:
    method = str(step.get("method", "auto") or "auto").lower()
    allowed = {"auto", "mean", "median", "mode", "constant", "zero"}
    if method not in allowed:
        raise ValueError(
            "impute method must be one of: " + ", ".join(sorted(allowed))
        )
    if method == "constant" and "value" not in step:
        raise ValueError("constant imputation requires a value")
    width = len(names)
    fills: list[dict[str, Any]] = []
    for index, name in enumerate(names):
        column = [row[index] for row in rows]
        present = [value for value in column if not _missing(value)]
        missing = len(column) - len(present)
        if method == "constant":
            resolved = "constant"
            fill = step.get("value")
        else:
            numeric = _numeric_column(column)
            chosen = method
            if chosen == "auto":
                chosen = "mean" if numeric else "mode"
            if chosen in ("mean", "median", "zero") and not numeric:
                raise ValueError(
                    "impute method '" + chosen + "' requires numeric column: "
                    + name
                )
            if not present:
                raise ValueError("column has no values to impute: " + name)
            if chosen == "zero":
                fill = 0.0
            elif chosen == "mean":
                fill = sum(float(value) for value in present) / len(present)
            elif chosen == "median":
                ordered = sorted(float(value) for value in present)
                middle = len(ordered) // 2
                if len(ordered) % 2:
                    fill = ordered[middle]
                else:
                    fill = (ordered[middle - 1] + ordered[middle]) / 2.0
            else:
                levels = _classes(present)
                fill = max(levels, key=lambda level: present.count(level))
            resolved = chosen
        fills.append({
            "name": name,
            "method": resolved,
            "value": fill,
            "missing": missing,
        })
    transformed = [
        [
            fills[index]["value"] if _missing(row[index]) else row[index]
            for index in range(width)
        ]
        for row in rows
    ]
    return {
        "op": "impute",
        "method": method,
        "fills": fills,
        "missing": sum(entry["missing"] for entry in fills),
    }, transformed


def _fit_encode(step: dict[str, Any], rows: list[list[Any]],
                names: list[str]) -> tuple[dict[str, Any], list[list[Any]]]:
    method = str(step.get("method", "onehot") or "onehot").lower()
    if method == "label":
        method = "ordinal"
    if method not in ("onehot", "ordinal"):
        raise ValueError("encode method must be 'onehot' or 'ordinal'")
    columns: list[dict[str, Any]] = []
    width = len(names)
    for index, name in enumerate(names):
        column = [row[index] for row in rows]
        if _numeric_column(column):
            continue
        levels = _classes(column)
        columns.append({
            "name": name,
            "levels": levels,
            "encoded": (
                [name + "=" + _label(level) for level in levels]
                if method == "onehot" else [name]
            ),
        })
    if method == "onehot":
        lookup = {entry["name"]: entry for entry in columns}
        output: list[str] = []
        for name in names:
            entry = lookup.get(name)
            if entry is None:
                output.append(name)
            else:
                output.extend(entry["encoded"])
        transformed: list[list[Any]] = []
        for row in rows:
            record: list[Any] = []
            for index, name in enumerate(names):
                entry = lookup.get(name)
                value = row[index]
                if entry is None:
                    record.append(value)
                    continue
                for level in entry["levels"]:
                    if _missing(value) and level is None:
                        record.append(1.0)
                    elif not _missing(value) and value == level:
                        record.append(1.0)
                    else:
                        record.append(0.0)
            transformed.append(record)
        return {
            "op": "encode",
            "method": method,
            "columns": columns,
            "names": output,
            "input_names": list(names),
        }, transformed
    lookup = {entry["name"]: entry for entry in columns}
    transformed = []
    for row in rows:
        record = []
        for index, name in enumerate(names):
            entry = lookup.get(name)
            if entry is None:
                record.append(row[index])
                continue
            value = row[index]
            levels = entry["levels"]
            record.append(
                float(levels.index(None)) if _missing(value)
                else float(levels.index(value))
            )
        transformed.append(record)
    return {
        "op": "encode",
        "method": method,
        "columns": columns,
        "names": list(names),
        "input_names": list(names),
    }, transformed


def _fit_scale(step: dict[str, Any], rows: list[list[Any]],
               names: list[str]) -> tuple[dict[str, Any], list[list[Any]]]:
    method = str(step.get("method", "standard") or "standard").lower()
    if method not in ("standard", "minmax"):
        raise ValueError("scale method must be 'standard' or 'minmax'")
    width = len(names)
    columns: list[dict[str, Any]] = []
    for index, name in enumerate(names):
        column = [row[index] for row in rows]
        if any(_missing(value) for value in column):
            raise ValueError("impute missing values before scaling: " + name)
        values = [
            _numeric(value, "scale requires numeric column: " + name)
            for value in column
        ]
        if method == "standard":
            center = sum(values) / len(values)
            variance = sum((value - center) ** 2 for value in values)
            deviation = math.sqrt(variance / (len(values) - 1)) if len(values) > 1 else 0.0
            scale = deviation if deviation > 0.0 else 1.0
        else:
            center = min(values)
            span = max(values) - center
            scale = span if span > 0.0 else 1.0
        columns.append({"name": name, "center": center, "scale": scale})
    transformed = [
        [
            (float(row[index]) - columns[index]["center"]) / columns[index]["scale"]
            for index in range(width)
        ]
        for row in rows
    ]
    return {
        "op": "scale",
        "method": method,
        "columns": columns,
    }, transformed


_FITTERS = {
    "impute": _fit_impute,
    "fillna": _fit_impute,
    "encode": _fit_encode,
    "scale": _fit_scale,
    "standardize": _fit_scale,
}


# ---------------------------------------------------------------------------
# Fit and transform
# ---------------------------------------------------------------------------

def fit_pipeline(steps: Iterable[Any], features: Any,
                 names: Any = None) -> dict[str, Any]:
    """Fit preprocessing steps and transform the training rows.

    ``steps`` is a list of records such as
    ``{"op": "impute", "method": "auto"}``. Steps run in order. Returns the
    fitted transformer with the transformed ``features``, the ``steps`` as
    fitted (including learned values) and the output column ``names``. The
    transformed rows keep whatever types the steps produce; add an ``encode``
    and a ``scale`` step before feeding them to a model.
    """
    rows = _rows(features)
    labels = _names(names, len(rows[0]))
    plan = list(steps or [])
    if not plan:
        raise ValueError("steps must not be empty")
    fitted: list[dict[str, Any]] = []
    output_names = list(labels)
    for step in plan:
        if not isinstance(step, dict):
            raise ValueError("each step must be a dict")
        op = str(step.get("op", "") or "").lower()
        if op not in _FITTERS:
            raise ValueError(
                "unknown step op: " + repr(step.get("op")) +
                " (expected impute, encode or scale)"
            )
        record, rows = _FITTERS[op](step, rows, output_names)
        output_names = record.get("names", output_names)
        fitted.append(record)
    return {
        "steps": fitted,
        "features": rows,
        "names": output_names,
        "input_names": labels,
        "n_features": len(output_names),
        "n": len(rows),
    }


def _apply_impute(step: dict[str, Any], rows: list[list[Any]],
                  width: int) -> list[list[Any]]:
    fills = step.get("fills") or []
    if len(fills) != width:
        raise ValueError("transformer does not match the number of features")
    return [
        [
            fills[index]["value"] if _missing(row[index]) else row[index]
            for index in range(width)
        ]
        for row in rows
    ]


def _apply_encode(step: dict[str, Any], rows: list[list[Any]],
                  width: int) -> tuple[list[list[Any]], int]:
    columns = {entry["name"]: entry for entry in (step.get("columns") or [])}
    method = step.get("method", "onehot")
    if method == "onehot":
        transformed: list[list[Any]] = []
        for row in rows:
            record: list[Any] = []
            for index in range(width):
                name = step["input_names"][index]
                entry = columns.get(name)
                value = row[index]
                if entry is None:
                    record.append(value)
                    continue
                for level in entry["levels"]:
                    if _missing(value) and level is None:
                        record.append(1.0)
                    elif not _missing(value) and value == level:
                        record.append(1.0)
                    else:
                        record.append(0.0)
            transformed.append(record)
        return transformed, len(step.get("names") or [])
    transformed = []
    for row in rows:
        record = []
        for index in range(width):
            name = step["input_names"][index]
            entry = columns.get(name)
            value = row[index]
            if entry is None:
                record.append(value)
                continue
            levels = entry["levels"]
            if _missing(value):
                record.append(float(levels.index(None)) if None in levels else -1.0)
            elif value in levels:
                record.append(float(levels.index(value)))
            else:
                record.append(-1.0)
        transformed.append(record)
    return transformed, width


def _apply_scale(step: dict[str, Any], rows: list[list[Any]],
                 width: int) -> list[list[Any]]:
    columns = step.get("columns") or []
    if len(columns) != width:
        raise ValueError("transformer does not match the number of features")
    return [
        [
            (float(row[index]) - columns[index]["center"]) / columns[index]["scale"]
            for index in range(width)
        ]
        for row in rows
    ]


def transform_pipeline(transformer: dict[str, Any],
                       features: Any) -> dict[str, Any]:
    """Apply a fitted transformer to new rows.

    The column order and count must match the data used during fitting. Unseen
    categories encode to all-zero one-hot rows, or ``-1`` for ordinal encoding.
    """
    if not isinstance(transformer, dict) or "steps" not in transformer:
        raise ValueError("transformer must be a fitted pipeline")
    rows = _rows(features)
    inputs = transformer.get("input_names") or []
    if len(rows[0]) != len(inputs):
        raise ValueError("transformer does not match the number of features")
    width = len(rows[0])
    for step in transformer["steps"]:
        op = step.get("op")
        if op == "impute":
            rows = _apply_impute(step, rows, width)
        elif op == "encode":
            rows, width = _apply_encode(step, rows, width)
        elif op == "scale":
            rows = _apply_scale(step, rows, width)
        else:
            raise ValueError("unknown fitted step op: " + repr(op))
    return {
        "features": rows,
        "names": list(transformer.get("names") or []),
    }


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_pipeline_namespace() -> dict[str, Any]:
    return {
        "fit_pipeline": fit_pipeline,
        "transform_pipeline": transform_pipeline,
    }
