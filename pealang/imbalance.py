"""Class-imbalance handling: balance reports, resampling and SMOTE.

This module rebalances classification data before fitting a model. It is pure
Python and dependency-free, and complements the estimators in
:mod:`pealang.trees` and :mod:`pealang.boosting`.

- :func:`class_balance` summarizes class counts and the imbalance ratio.
- :func:`random_oversample` duplicates random minority rows.
- :func:`random_undersample` drops random majority rows.
- :func:`smote` synthesizes minority rows by interpolating between a row and
  one of its nearest same-class neighbors.

All randomness is seeded, so the same seed produces the same rows.
"""

from __future__ import annotations

import math
import random
from typing import Any, Iterable

from .trees import _classes, _design


# ---------------------------------------------------------------------------
# Balance report
# ---------------------------------------------------------------------------

def _counts(labels: list[Any]) -> list[dict[str, Any]]:
    total = len(labels)
    classes = _classes(labels)
    table: list[dict[str, Any]] = []
    for label in classes:
        count = labels.count(label)
        table.append({
            "class": label,
            "count": count,
            "share": count / total if total else 0.0,
        })
    return table


def class_balance(target: Iterable[Any]) -> dict[str, Any]:
    """Summarize class counts, shares and the majority-to-minority ratio.

    Returns ``classes`` in sorted order, a ``counts`` table and the
    ``imbalance_ratio`` (largest class divided by smallest). A ratio near ``1``
    means the classes are balanced; large values flag rare classes.
    """
    labels = list(target or [])
    if not labels:
        raise ValueError("target is required")
    table = _counts(labels)
    largest = max(entry["count"] for entry in table)
    smallest = min(entry["count"] for entry in table)
    return {
        "n": len(labels),
        "classes": [entry["class"] for entry in table],
        "counts": table,
        "majority": max(table, key=lambda entry: entry["count"])["class"],
        "minority": min(table, key=lambda entry: entry["count"])["class"],
        "imbalance_ratio": largest / smallest if smallest else float("inf"),
    }


def _validate(features: Any, target: Iterable[Any]) -> tuple[list[list[float]], list[Any]]:
    rows = _design(features)
    labels = list(target or [])
    if len(labels) != len(rows):
        raise ValueError("features and target lengths must match")
    return rows, labels


def _result(method: str, rows: list[list[float]], labels: list[Any],
            original: int, seed: Any) -> dict[str, Any]:
    return {
        "method": method,
        "features": rows,
        "target": labels,
        "n": len(labels),
        "added": max(0, len(labels) - original),
        "removed": max(0, original - len(labels)),
        "seed": seed,
    }


# ---------------------------------------------------------------------------
# Random resampling
# ---------------------------------------------------------------------------

def random_oversample(features: Any, target: Iterable[Any],
                      seed: Any = 0) -> dict[str, Any]:
    """Duplicate random minority rows until every class matches the majority.

    Sampling is with replacement and seeded. The original rows keep their order
    and synthetic copies are appended.
    """
    rows, labels = _validate(features, target)
    classes = _classes(labels)
    counts = {label: labels.count(label) for label in classes}
    largest = max(counts.values())
    rng = random.Random(seed)
    out_rows = [list(row) for row in rows]
    out_labels = list(labels)
    for label in classes:
        pool = [index for index, value in enumerate(labels) if value == label]
        for _ in range(largest - counts[label]):
            source = rng.choice(pool)
            out_rows.append(list(rows[source]))
            out_labels.append(label)
    return _result("random_oversample", out_rows, out_labels, len(labels), seed)


def random_undersample(features: Any, target: Iterable[Any],
                       seed: Any = 0) -> dict[str, Any]:
    """Drop random majority rows until every class matches the minority.

    Sampling is without replacement and seeded. Kept rows stay in their original
    order.
    """
    rows, labels = _validate(features, target)
    classes = _classes(labels)
    counts = {label: labels.count(label) for label in classes}
    smallest = min(counts.values())
    rng = random.Random(seed)
    keep: list[int] = []
    for label in classes:
        pool = [index for index, value in enumerate(labels) if value == label]
        if counts[label] > smallest:
            chosen = sorted(rng.sample(pool, smallest))
        else:
            chosen = pool
        keep.extend(chosen)
    keep.sort()
    out_rows = [list(rows[index]) for index in keep]
    out_labels = [labels[index] for index in keep]
    return _result("random_undersample", out_rows, out_labels, len(labels), seed)


# ---------------------------------------------------------------------------
# SMOTE
# ---------------------------------------------------------------------------

def _distance(left: list[float], right: list[float]) -> float:
    total = 0.0
    for a, b in zip(left, right):
        delta = a - b
        total += delta * delta
    return math.sqrt(total)


def _neighbors(rows: list[list[float]], pool: list[int], index: int,
               k: int) -> list[int]:
    point = rows[index]
    ranked = sorted(
        (other for other in pool if other != index),
        key=lambda other: (_distance(point, rows[other]), other),
    )
    return ranked[:k]


def smote(features: Any, target: Iterable[Any], k: int = 5,
          seed: Any = 0) -> dict[str, Any]:
    """Synthesize minority rows by interpolating between nearest neighbors.

    Every class below the majority count is oversampled to match it. For each
    synthetic row SMOTE picks a base row, finds its ``k`` nearest same-class
    neighbors, picks one at random, and places the new row a random fraction of
    the way from the base to that neighbor. When a class has a single row there
    is nothing to interpolate, so the row is duplicated instead.

    ``k`` is capped at ``count - 1`` for each class. Distances use Euclidean
    metric on the numeric feature columns, so encode categorical predictors
    first.
    """
    rows, labels = _validate(features, target)
    neighbors = int(k)
    if neighbors < 1:
        raise ValueError("k must be at least 1")
    classes = _classes(labels)
    counts = {label: labels.count(label) for label in classes}
    largest = max(counts.values())
    rng = random.Random(seed)
    out_rows = [list(row) for row in rows]
    out_labels = list(labels)
    for label in classes:
        pool = [index for index, value in enumerate(labels) if value == label]
        needed = largest - counts[label]
        if needed <= 0:
            continue
        depth = min(neighbors, len(pool) - 1)
        for _ in range(needed):
            base = rng.choice(pool)
            if depth < 1:
                out_rows.append(list(rows[base]))
                out_labels.append(label)
                continue
            options = _neighbors(rows, pool, base, depth)
            partner = rng.choice(options)
            gap = rng.random()
            out_rows.append([
                rows[base][position]
                + gap * (rows[partner][position] - rows[base][position])
                for position in range(len(rows[base]))
            ])
            out_labels.append(label)
    return _result("smote", out_rows, out_labels, len(labels), seed)


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_imbalance_namespace() -> dict[str, Any]:
    return {
        "class_balance": class_balance,
        "random_oversample": random_oversample,
        "random_undersample": random_undersample,
        "smote": smote,
    }
