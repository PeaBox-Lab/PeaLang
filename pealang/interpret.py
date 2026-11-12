"""Model interpretation: permutation importance and partial dependence.

This module explains fitted :mod:`pealang.trees` and :mod:`pealang.boosting`
models. It replaces the scikit-learn ``permutation_importance`` and
``PartialDependenceDisplay`` workflow with pure Python.

Permutation importance measures how much a metric drops when a column is
shuffled, which is less biased toward high-cardinality features than split-gain
importance. Partial dependence traces how the average prediction moves as one
feature sweeps its observed range.
"""

from __future__ import annotations

import random
from typing import Any, Iterable

from .numerics import mean, std
from .selection import (_higher_is_better, _predict, _resolve_scoring, _score)
from .trees import _design, _task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _kind(model: dict[str, Any], task: Any) -> str:
    if str(task or "auto").lower() == "auto":
        stored = model.get("task")
        if stored:
            return _task(stored)
        raise ValueError("task is required when the model has no task")
    return _task(task)


def _width(rows: list[list[float]]) -> int:
    return len(rows[0])


def _check_model(model: Any) -> dict[str, Any]:
    if not isinstance(model, dict):
        raise ValueError("model must be a fitted model record")
    if not model.get("estimator"):
        raise ValueError("model must be a fitted model record")
    return model


def _column_indices(columns: Any, width: int,
                    names: list[str] | None) -> list[int]:
    if columns is None:
        return list(range(width))
    if isinstance(columns, (str, int)):
        columns = [columns]
    chosen: list[int] = []
    for entry in columns:
        if isinstance(entry, str):
            if not names:
                raise ValueError("column names require feature names")
            if entry not in names:
                raise ValueError("unknown feature: " + entry)
            index = names.index(entry)
        else:
            index = int(entry)
            if index < 0 or index >= width:
                raise ValueError("column index out of range: " + str(index))
        if index not in chosen:
            chosen.append(index)
    if not chosen:
        raise ValueError("columns must not be empty")
    return chosen


def _feature_names(names: Any, width: int) -> list[str]:
    if names is None:
        return ["x" + str(index + 1) for index in range(width)]
    labels = [str(name) for name in names]
    if len(labels) != width:
        raise ValueError("feature names must match the number of features")
    return labels


def _grid(values: list[float], size: int) -> list[float]:
    low = min(values)
    high = max(values)
    if size < 2:
        raise ValueError("grid_size must be at least 2")
    if high == low:
        return [low] * size
    step = (high - low) / (size - 1)
    return [low + step * index for index in range(size)]


# ---------------------------------------------------------------------------
# Permutation importance
# ---------------------------------------------------------------------------

def permutation_importance(model: dict[str, Any], features: Any,
                           target: Iterable[Any], task: Any = "auto",
                           n_repeats: int = 5, seed: Any = 0,
                           scoring: Any = "auto",
                           names: Any = None) -> dict[str, Any]:
    """Measure how much each feature contributes by shuffling it.

    The model is scored once as a baseline, then each feature column is
    permuted ``n_repeats`` times and the metric is recomputed. Importance is the
    baseline minus the shuffled score for higher-is-better metrics, and the
    shuffled score minus the baseline for error metrics. Returns a sorted
    ``importances`` table with the mean and spread across repeats.
    """
    _check_model(model)
    rows = _design(features)
    labels = list(target or [])
    if len(labels) != len(rows):
        raise ValueError("features and target lengths must match")
    kind = _kind(model, task)
    repeats = int(n_repeats)
    if repeats < 1:
        raise ValueError("n_repeats must be at least 1")
    width = _width(rows)
    labels_out = _feature_names(names, width)
    metric = _resolve_scoring(scoring, kind)
    higher = _higher_is_better(metric)
    baseline = _score(
        kind, metric, labels, _predict(model["estimator"], model, rows)
    )
    rng = random.Random(seed)
    importances: list[dict[str, Any]] = []
    for index in range(width):
        column = [row[index] for row in rows]
        values: list[float] = []
        for _ in range(repeats):
            order = list(range(len(rows)))
            rng.shuffle(order)
            shuffled = [list(row) for row in rows]
            for position, source in enumerate(order):
                shuffled[position][index] = column[source]
            score = _score(
                kind, metric, labels,
                _predict(model["estimator"], model, shuffled),
            )
            values.append(baseline - score if higher else score - baseline)
        spread = float(std(values, True) or 0.0)
        importances.append({
            "feature": labels_out[index],
            "mean": float(mean(values)),
            "std": spread,
            "values": values,
        })
    importances.sort(key=lambda entry: (-entry["mean"], entry["feature"]))
    return {
        "estimator": model.get("estimator"),
        "task": kind,
        "scoring": metric,
        "baseline": baseline,
        "higher_is_better": higher,
        "n_repeats": repeats,
        "seed": seed,
        "importances": importances,
    }


# ---------------------------------------------------------------------------
# Partial dependence
# ---------------------------------------------------------------------------

def partial_dependence(model: dict[str, Any], features: Any,
                       columns: Any = None, grid_size: int = 10,
                       task: Any = "auto",
                       names: Any = None) -> dict[str, Any]:
    """Trace the average prediction as one feature sweeps its range.

    For every selected column a grid of ``grid_size`` evenly spaced values
    between the observed minimum and maximum is built. At each grid point the
    column is set for every row and the model is scored, then predictions are
    averaged. Regression curves carry ``average``; classification curves also
    carry ``classes`` and per-class ``probabilities``. ``average`` is the mean
    probability of the last class, which is the positive class for binary
    problems.
    """
    _check_model(model)
    rows = _design(features)
    kind = _kind(model, task)
    width = _width(rows)
    labels_out = _feature_names(names, width)
    chosen = _column_indices(columns, width, labels_out)
    size = int(grid_size)
    if size < 2:
        raise ValueError("grid_size must be at least 2")
    curves: list[dict[str, Any]] = []
    for index in chosen:
        values = _grid([row[index] for row in rows], size)
        averages: list[float] = []
        per_class: list[list[float]] | None = None
        classes: list[Any] | None = None
        for value in values:
            probe = [list(row) for row in rows]
            for row in probe:
                row[index] = value
            result = _predict(model["estimator"], model, probe)
            if kind == "regression":
                averages.append(float(mean(result["predicted"])))
                continue
            probabilities = result.get("probabilities") or []
            if not probabilities:
                raise ValueError(
                    "partial_dependence needs predicted probabilities"
                )
            classes = list(result.get("classes") or [])
            if per_class is None:
                per_class = [[] for _ in classes]
            for position in range(len(classes)):
                per_class[position].append(
                    float(mean(row[position] for row in probabilities))
                )
            averages.append(
                float(mean(row[-1] for row in probabilities))
            )
        curve: dict[str, Any] = {
            "feature": labels_out[index],
            "values": values,
            "average": averages,
        }
        if kind == "classification":
            curve["classes"] = classes
            curve["probabilities"] = per_class
        curves.append(curve)
    return {
        "estimator": model.get("estimator"),
        "task": kind,
        "grid_size": size,
        "curves": curves,
    }


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_interpret_namespace() -> dict[str, Any]:
    return {
        "permutation_importance": permutation_importance,
        "partial_dependence": partial_dependence,
    }
