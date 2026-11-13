"""Smoothed target (mean) encoding for categorical columns.

High-cardinality categories blow up one-hot encoding: a ``store`` column with
500 stores becomes 500 columns, most of them almost empty. Target encoding
replaces each category with the smoothed mean of the target for that category,
so the column stays one numeric feature wide.

The helpers here are pure Python and dependency-free. The same maths backs the
``target`` pipeline step, which fits the category means on training data and
reapplies them to new rows.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

DEFAULT_SMOOTHING = 10.0


def _missing(value: Any) -> bool:
    return value is None or (
        isinstance(value, float) and math.isnan(value)
    )


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and not (isinstance(value, float) and math.isnan(value))
    )


def _key(value: Any) -> tuple[str, Any]:
    """Return a stable lookup key without requiring JSON-safe keys."""
    if _missing(value):
        return ("missing", "")
    try:
        hash(value)
    except TypeError:
        return (type(value).__name__, repr(value))
    return (type(value).__name__, value)


def _order(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _coerce_target(target: Any, n: int) -> tuple[list[float], str, list[Any]]:
    """Validate a target vector and return numeric values plus metadata.

    Numeric targets are used as-is. Categorical targets are accepted when they
    have exactly two classes, which are mapped to ``0`` and ``1`` in sorted
    order; the encoded mean is then the proportion of the second class.
    """
    if target is None:
        raise ValueError("target is required for target encoding")
    if isinstance(target, (str, bytes)) or not isinstance(target, Iterable):
        raise ValueError("target must be an iterable of values")
    values = list(target)
    if len(values) != n:
        raise ValueError(
            "target length must match the number of values: "
            + str(len(values)) + " vs " + str(n)
        )
    for index, value in enumerate(values):
        if _missing(value):
            raise ValueError(
                "target must be complete for target encoding; missing value "
                "at row " + str(index)
            )
    if all(_is_number(value) for value in values):
        return [float(value) for value in values], "numeric", []
    classes: list[Any] = []
    seen: set[Any] = set()
    for value in values:
        key = _key(value)
        if key in seen:
            continue
        seen.add(key)
        classes.append(value)
    classes.sort(key=_order)
    if len(classes) != 2:
        raise ValueError(
            "target encoding requires a numeric or binary target (found "
            + str(len(classes)) + " classes); encode multiclass targets first"
        )
    negative = _key(classes[0])
    encoded = [
        0.0 if _key(value) == negative else 1.0 for value in values
    ]
    return encoded, "binary", classes


def _options(smoothing: Any, min_count: Any) -> tuple[float, int]:
    if isinstance(smoothing, bool):
        raise ValueError("smoothing must be a non-negative number")
    try:
        weight = float(smoothing)
    except (TypeError, ValueError):
        raise ValueError("smoothing must be a non-negative number") from None
    if not math.isfinite(weight) or weight < 0.0:
        raise ValueError("smoothing must be a non-negative number")
    if isinstance(min_count, bool):
        raise ValueError("min_count must be at least 1")
    try:
        count = int(min_count)
    except (TypeError, ValueError):
        raise ValueError("min_count must be at least 1") from None
    if count < 1 or count != min_count:
        raise ValueError("min_count must be at least 1")
    return weight, count


def _levels(values: list[Any], outcomes: list[float], prior: float,
            smoothing: float, min_count: int) -> list[dict[str, Any]]:
    """Group rows by category and return the encoded level records."""
    groups: dict[tuple[str, Any], dict[str, Any]] = {}
    for value, outcome in zip(values, outcomes):
        key = _key(value)
        entry = groups.get(key)
        if entry is None:
            entry = {"level": value, "outcomes": []}
            groups[key] = entry
        entry["outcomes"].append(outcome)
    records: list[dict[str, Any]] = []
    for entry in sorted(groups.values(), key=lambda item: _order(item["level"])):
        outcomes = entry["outcomes"]
        count = len(outcomes)
        mean = sum(outcomes) / count
        if count < min_count:
            encoded = prior
        else:
            encoded = (count * mean + smoothing * prior) / (count + smoothing)
        records.append({
            "level": entry["level"],
            "count": count,
            "mean": mean,
            "encoded": encoded,
        })
    return records


def target_encode(values: Any, target: Any, smoothing: Any = DEFAULT_SMOOTHING,
                  min_count: Any = 1) -> dict[str, Any]:
    """Fit a smoothed target encoder for one categorical column.

    Each level is encoded as ``(count * mean + smoothing * prior) /
    (count + smoothing)``. Levels seen fewer than ``min_count`` times, and
    unseen levels at apply time, fall back to the overall target mean (the
    prior). ``smoothing = 0`` uses the raw level mean.

    Returns ``{method, smoothing, min_count, prior, kind, classes, levels, n}``
    where ``levels`` holds ``{level, count, mean, encoded}`` records in sorted
    order.

    ```pea
    let encoder = stats.target_encode(stores, sales, 10.0, 1)
    print encoder["prior"]
    print stats.target_apply(encoder, ["new store"])
    ```
    """
    if values is None or isinstance(values, (str, bytes)):
        raise ValueError("values must be an iterable of categories")
    items = list(values)
    if not items:
        raise ValueError("values are required")
    outcomes, kind, classes = _coerce_target(target, len(items))
    weight, count = _options(smoothing, min_count)
    prior = sum(outcomes) / len(outcomes)
    return {
        "method": "mean",
        "smoothing": weight,
        "min_count": count,
        "prior": prior,
        "kind": kind,
        "classes": classes,
        "levels": _levels(items, outcomes, prior, weight, count),
        "n": len(items),
    }


def target_apply(encoder: Any, values: Any) -> list[float]:
    """Encode categories with a fitted target encoder.

    Unseen levels and missing values encode to the fitted prior.
    """
    if not isinstance(encoder, dict) or "prior" not in encoder:
        raise ValueError("encoder must be fitted by target_encode")
    if values is None or isinstance(values, (str, bytes)):
        raise ValueError("values must be an iterable of categories")
    items = list(values)
    if not items:
        raise ValueError("values are required")
    lookup: dict[tuple[str, Any], float] = {}
    for entry in encoder.get("levels") or []:
        lookup[_key(entry.get("level"))] = float(entry.get("encoded"))
    prior = float(encoder["prior"])
    return [lookup.get(_key(value), prior) for value in items]


def build_target_namespace() -> dict[str, Any]:
    return {
        "target_encode": target_encode,
        "target_apply": target_apply,
    }
