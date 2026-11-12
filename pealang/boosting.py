"""Gradient boosted trees.

This module is the boosted-tree layer above :mod:`pealang.trees`. It provides
gradient boosting for regression, binary classification and multiclass
classification, with shrinkage, row subsampling and feature importance.
Everything is pure Python and dependency-free.
"""

from __future__ import annotations

import math
import random
from typing import Any, Iterable, Sequence

from .numerics import mean
from .trees import (decision_tree, _classes, _design, _feature_count, _task,
                    _walk, tree_feature_importance)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sigmoid(value: float) -> float:
    if value >= 0.0:
        return 1.0 / (1.0 + math.exp(-value))
    scaled = math.exp(value)
    return scaled / (1.0 + scaled)


def _softmax(values: Sequence[float]) -> list[float]:
    largest = max(values)
    exps = [math.exp(value - largest) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


def _assign_leaves(node: dict[str, Any], rows: list[list[float]],
                   indices: list[int], residual: list[float],
                   weight: list[float], multiplier: float) -> None:
    """Replace leaf values with a Newton step computed on the given rows."""
    if node["leaf"]:
        numerator = sum(residual[i] for i in indices)
        denominator = sum(weight[i] for i in indices)
        node["value"] = (
            multiplier * numerator / denominator if denominator > 0.0 else 0.0
        )
        return
    feature = node["feature"]
    threshold = node["threshold"]
    left = [i for i in indices if rows[i][feature] <= threshold]
    right = [i for i in indices if rows[i][feature] > threshold]
    _assign_leaves(node["left"], rows, left, residual, weight, multiplier)
    _assign_leaves(node["right"], rows, right, residual, weight, multiplier)


def _stage_trees(stages: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [tree for stage in stages for tree in stage]


def _importance(stages: list[list[dict[str, Any]]], width: int) -> list[float]:
    trees = _stage_trees(stages)
    if not trees:
        return [0.0] * width
    totals = [0.0] * width
    for tree in trees:
        for index, value in enumerate(tree["feature_importances"]):
            totals[index] += value
    total = sum(totals)
    if total > 0.0:
        return [value / total for value in totals]
    return totals


# ---------------------------------------------------------------------------
# Gradient boosting
# ---------------------------------------------------------------------------

def gradient_boosting(features: Any, target: Iterable[Any],
                      task: str = "regression", n_estimators: int = 100,
                      learning_rate: float = 0.1, max_depth: int | None = 3,
                      min_samples_split: int = 2, min_samples_leaf: int = 1,
                      subsample: float = 1.0, max_features: Any = None,
                      seed: Any = 0) -> dict[str, Any]:
    """Fit a gradient boosted tree ensemble.

    Regression uses squared error. Classification uses logistic loss for two
    classes and softmax loss for more than two. Each stage fits regression
    trees to the negative gradient and applies a Newton leaf update, then
    shrinks the update by ``learning_rate``. ``subsample`` below 1 fits each
    stage on a random row subset.
    """
    rows = _design(features)
    n = len(rows)
    kind = _task(task)
    regression = kind == "regression"
    labels = [float(value) for value in (target or [])] if regression else list(target or [])
    if len(labels) != n:
        raise ValueError("features and target lengths must match")
    count = int(n_estimators)
    if count < 1:
        raise ValueError("n_estimators must be at least 1")
    rate = float(learning_rate)
    if not rate > 0.0:
        raise ValueError("learning_rate must be positive")
    depth = 100 if max_depth is None else int(max_depth)
    if depth < 1:
        raise ValueError("max_depth must be at least 1")
    split_min = int(min_samples_split)
    if split_min < 2:
        raise ValueError("min_samples_split must be at least 2")
    leaf_min = int(min_samples_leaf)
    if leaf_min < 1:
        raise ValueError("min_samples_leaf must be at least 1")
    fraction = float(subsample)
    if not 0.0 < fraction <= 1.0:
        raise ValueError("subsample must be between 0 and 1")
    width = len(rows[0])
    feature_count = _feature_count(max_features, width)
    rng = random.Random(seed)

    classes = [] if regression else _classes(labels)
    if not regression and len(classes) < 2:
        raise ValueError("classification requires at least two classes")

    stages: list[list[dict[str, Any]]] = []

    if regression:
        base: Any = mean(labels)
        current = [base] * n
        for _ in range(count):
            residual = [labels[i] - current[i] for i in range(n)]
            sample = _sample_indices(n, fraction, rng)
            tree = decision_tree(
                [rows[i] for i in sample],
                [residual[i] for i in sample],
                "regression",
                depth,
                split_min,
                leaf_min,
                max_features,
                rng.randrange(2 ** 31),
            )
            for row_index in range(n):
                current[row_index] += rate * float(_walk(tree["tree"], rows[row_index])["value"])
            stages.append([tree])

    elif len(classes) == 2:
        positive = classes[1]
        binary = [1.0 if label == positive else 0.0 for label in labels]
        prior = min(max(mean(binary), 1e-6), 1.0 - 1e-6)
        base = math.log(prior / (1.0 - prior))
        current = [base] * n
        for _ in range(count):
            probabilities = [_sigmoid(value) for value in current]
            residual = [binary[i] - probabilities[i] for i in range(n)]
            weight = [
                max(probabilities[i] * (1.0 - probabilities[i]), 1e-6)
                for i in range(n)
            ]
            sample = _sample_indices(n, fraction, rng)
            tree = decision_tree(
                [rows[i] for i in sample],
                [residual[i] for i in sample],
                "regression",
                depth,
                split_min,
                leaf_min,
                max_features,
                rng.randrange(2 ** 31),
            )
            _assign_leaves(
                tree["tree"],
                [rows[i] for i in sample],
                list(range(len(sample))),
                [residual[i] for i in sample],
                [weight[i] for i in sample],
                1.0,
            )
            for row_index in range(n):
                current[row_index] += rate * float(_walk(tree["tree"], rows[row_index])["value"])
            stages.append([tree])

    else:
        size = len(classes)
        position = {label: index for index, label in enumerate(classes)}
        indicators = [
            [1.0 if label == classes[k] else 0.0 for k in range(size)]
            for label in labels
        ]
        base = [
            math.log(max(sum(indicators[i][k] for i in range(n)) / n, 1e-6))
            for k in range(size)
        ]
        current = [[base[k]] * n for k in range(size)]
        multiplier = (size - 1.0) / size
        for _ in range(count):
            probabilities = [
                _softmax([current[k][i] for k in range(size)])
                for i in range(n)
            ]
            residual = [
                [indicators[i][k] - probabilities[i][k] for k in range(size)]
                for i in range(n)
            ]
            weight = [
                [max(probabilities[i][k] * (1.0 - probabilities[i][k]), 1e-6)
                 for k in range(size)]
                for i in range(n)
            ]
            sample = _sample_indices(n, fraction, rng)
            trees = []
            for k in range(size):
                tree = decision_tree(
                    [rows[i] for i in sample],
                    [residual[i][k] for i in sample],
                    "regression",
                    depth,
                    split_min,
                    leaf_min,
                    max_features,
                    rng.randrange(2 ** 31),
                )
                _assign_leaves(
                    tree["tree"],
                    [rows[i] for i in sample],
                    list(range(len(sample))),
                    [residual[i][k] for i in sample],
                    [weight[i][k] for i in sample],
                    multiplier,
                )
                trees.append(tree)
            for row_index in range(n):
                for k in range(size):
                    current[k][row_index] += rate * float(
                        _walk(trees[k]["tree"], rows[row_index])["value"]
                    )
            stages.append(trees)

    return {
        "estimator": "gradient_boosting",
        "task": kind,
        "stages": stages,
        "n_estimators": count,
        "learning_rate": rate,
        "base": base,
        "classes": classes,
        "feature_importances": _importance(stages, width),
        "n_features": width,
        "n": n,
        "max_depth": depth,
        "min_samples_split": split_min,
        "min_samples_leaf": leaf_min,
        "subsample": fraction,
        "max_features": max_features,
        "seed": seed,
    }


def _sample_indices(n: int, fraction: float, rng: random.Random) -> list[int]:
    if fraction >= 1.0:
        return list(range(n))
    size = max(1, int(math.ceil(n * fraction)))
    return sorted(rng.sample(range(n), size))


def predict_boosting(model: dict[str, Any], features: Any) -> dict[str, Any]:
    """Predict with a fitted gradient boosted ensemble."""
    rows = _design(features)
    stages = model["stages"]
    if not stages:
        raise ValueError("the model has no boosting stages")
    rate = model["learning_rate"]
    kind = model.get("task")

    if kind == "regression":
        base = float(model["base"])
        predicted = []
        for row in rows:
            total = base
            for stage in stages:
                total += rate * float(_walk(stage[0]["tree"], row)["value"])
            predicted.append(total)
        return {"predicted": predicted}

    classes = model["classes"]
    if len(classes) == 2:
        base = float(model["base"])
        predicted = []
        probabilities = []
        for row in rows:
            total = base
            for stage in stages:
                total += rate * float(_walk(stage[0]["tree"], row)["value"])
            probability = _sigmoid(total)
            probabilities.append([1.0 - probability, probability])
            predicted.append(classes[1] if probability >= 0.5 else classes[0])
        return {
            "predicted": predicted,
            "probabilities": probabilities,
            "classes": list(classes),
        }

    size = len(classes)
    base = [float(value) for value in model["base"]]
    predicted = []
    probabilities = []
    for row in rows:
        raw = list(base)
        for stage in stages:
            for k in range(size):
                raw[k] += rate * float(_walk(stage[k]["tree"], row)["value"])
        distribution = _softmax(raw)
        probabilities.append(distribution)
        position = max(range(size), key=lambda slot: (distribution[slot], -slot))
        predicted.append(classes[position])
    return {
        "predicted": predicted,
        "probabilities": probabilities,
        "classes": list(classes),
    }


def boosting_feature_importance(model: dict[str, Any],
                                names: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """Rank features by their averaged importance across boosting stages."""
    return tree_feature_importance(model, names)


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_boosting_namespace() -> dict[str, Any]:
    return {
        "gradient_boosting": gradient_boosting,
        "predict_boosting": predict_boosting,
        "boosting_feature_importance": boosting_feature_importance,
    }
