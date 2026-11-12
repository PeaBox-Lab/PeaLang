"""Decision trees and random forests.

This module is the tree-based modeling layer above :mod:`pealang.modeling`. It
provides CART regression and classification trees, prediction, feature
importances, and bagged random forests with out-of-bag scoring. Everything is
pure Python and dependency-free.
"""

from __future__ import annotations

import math
import random
from typing import Any, Iterable, Sequence

from .numerics import mean


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _design(features: Any) -> list[list[float]]:
    rows = [[float(value) for value in row] for row in (features or [])]
    if not rows:
        raise ValueError("features are required")
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise ValueError("feature rows must be non-empty and equal length")
    return rows


def _task(name: Any) -> str:
    key = str(name or "regression").lower()
    if key in ("regression", "regressor", "continuous"):
        return "regression"
    if key in ("classification", "classifier", "class"):
        return "classification"
    raise ValueError("task must be 'regression' or 'classification'")


def _classes(values: Iterable[Any]) -> list[Any]:
    out: list[Any] = []
    for value in values:
        if value not in out:
            out.append(value)
    return sorted(out, key=lambda value: (str(type(value)), repr(value)))


def _feature_count(value: Any, width: int) -> int:
    if value is None:
        return width
    if isinstance(value, str):
        key = value.lower()
        if key in ("all", "none"):
            return width
        if key == "sqrt":
            return max(1, int(math.sqrt(width)))
        if key == "log2":
            return max(1, int(math.log2(width)))
        raise ValueError("max_features must be an int, float, 'sqrt' or 'log2'")
    if isinstance(value, float):
        if not 0.0 < value <= 1.0:
            raise ValueError("a float max_features must be between 0 and 1")
        return max(1, min(width, int(math.ceil(width * value))))
    count = int(value)
    if count < 1:
        raise ValueError("max_features must be at least 1")
    return min(width, count)


def _leaf_value(indices: list[int], target: list[Any], regression: bool,
                classes: list[Any]) -> dict[str, Any]:
    if regression:
        return {
            "leaf": True,
            "value": mean([target[i] for i in indices]),
            "n": len(indices),
        }
    counts = {label: 0 for label in classes}
    for i in indices:
        counts[target[i]] += 1
    total = len(indices)
    best = sorted(
        classes,
        key=lambda label: (-counts[label], str(type(label)), repr(label)),
    )[0]
    return {
        "leaf": True,
        "value": best,
        "probabilities": [counts[label] / total for label in classes],
        "n": total,
    }


def _cost(indices: list[int], target: list[Any], regression: bool) -> float:
    if not indices:
        return 0.0
    if regression:
        values = [float(target[i]) for i in indices]
        center = sum(values) / len(values)
        return sum((value - center) ** 2 for value in values)
    counts: dict[Any, int] = {}
    for i in indices:
        counts[target[i]] = counts.get(target[i], 0) + 1
    total = len(indices)
    return (1.0 - sum((count / total) ** 2 for count in counts.values())) * total


def _best_split(rows: list[list[float]], target: list[Any], indices: list[int],
                candidates: list[int], regression: bool, parent_cost: float,
                min_samples_leaf: int) -> tuple[int, float, float] | None:
    best_feature = -1
    best_threshold = 0.0
    best_gain = 1e-12
    for feature in candidates:
        ordered = sorted(indices, key=lambda i: rows[i][feature])
        count = len(ordered)
        if regression:
            values = [float(target[i]) for i in ordered]
            total = sum(values)
            total_sq = sum(value * value for value in values)
            left_sum = 0.0
            left_sq = 0.0
            for position in range(count - 1):
                left_sum += values[position]
                left_sq += values[position] * values[position]
                if rows[ordered[position]][feature] == rows[ordered[position + 1]][feature]:
                    continue
                left_n = position + 1
                right_n = count - left_n
                if left_n < min_samples_leaf or right_n < min_samples_leaf:
                    continue
                left_cost = left_sq - left_sum * left_sum / left_n
                right_sum = total - left_sum
                right_sq = total_sq - left_sq
                right_cost = right_sq - right_sum * right_sum / right_n
                gain = parent_cost - (left_cost + right_cost)
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature
                    best_threshold = (
                        rows[ordered[position]][feature]
                        + rows[ordered[position + 1]][feature]
                    ) / 2.0
        else:
            left_counts: dict[Any, int] = {}
            right_counts: dict[Any, int] = {}
            for i in ordered:
                right_counts[target[i]] = right_counts.get(target[i], 0) + 1
            left_n = 0
            for position in range(count - 1):
                label = target[ordered[position]]
                left_counts[label] = left_counts.get(label, 0) + 1
                right_counts[label] -= 1
                left_n += 1
                if rows[ordered[position]][feature] == rows[ordered[position + 1]][feature]:
                    continue
                right_n = count - left_n
                if left_n < min_samples_leaf or right_n < min_samples_leaf:
                    continue
                left_gini = 1.0 - sum(
                    (value / left_n) ** 2 for value in left_counts.values()
                )
                right_gini = 1.0 - sum(
                    (value / right_n) ** 2 for value in right_counts.values()
                )
                gain = parent_cost - (left_gini * left_n + right_gini * right_n)
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature
                    best_threshold = (
                        rows[ordered[position]][feature]
                        + rows[ordered[position + 1]][feature]
                    ) / 2.0
    if best_feature < 0:
        return None
    return best_feature, best_threshold, best_gain


def _grow(rows: list[list[float]], target: list[Any], indices: list[int],
          regression: bool, classes: list[Any], depth: int, max_depth: int,
          min_samples_split: int, min_samples_leaf: int,
          feature_count: int, rng: random.Random) -> dict[str, Any]:
    node_n = len(indices)
    if depth >= max_depth or node_n < min_samples_split:
        return _leaf_value(indices, target, regression, classes)
    if regression:
        values = [float(target[i]) for i in indices]
        if max(values) == min(values):
            return _leaf_value(indices, target, regression, classes)
    elif len({target[i] for i in indices}) == 1:
        return _leaf_value(indices, target, regression, classes)

    parent_cost = _cost(indices, target, regression)
    width = len(rows[0])
    if feature_count >= width:
        candidates = list(range(width))
    else:
        candidates = sorted(rng.sample(range(width), feature_count))
    split = _best_split(
        rows, target, indices, candidates, regression, parent_cost,
        max(1, min_samples_leaf),
    )
    if split is None:
        return _leaf_value(indices, target, regression, classes)
    feature, threshold, gain = split
    left = [i for i in indices if rows[i][feature] <= threshold]
    right = [i for i in indices if rows[i][feature] > threshold]
    if not left or not right:
        return _leaf_value(indices, target, regression, classes)
    return {
        "leaf": False,
        "feature": feature,
        "threshold": threshold,
        "gain": gain,
        "n": node_n,
        "left": _grow(
            rows, target, left, regression, classes, depth + 1, max_depth,
            min_samples_split, min_samples_leaf, feature_count, rng,
        ),
        "right": _grow(
            rows, target, right, regression, classes, depth + 1, max_depth,
            min_samples_split, min_samples_leaf, feature_count, rng,
        ),
    }


def _walk(node: dict[str, Any], row: list[float]) -> dict[str, Any]:
    while not node["leaf"]:
        node = node["left"] if row[node["feature"]] <= node["threshold"] else node["right"]
    return node


def _collect_importance(node: dict[str, Any], accum: list[float]) -> None:
    if node["leaf"]:
        return
    accum[node["feature"]] += node["gain"]
    _collect_importance(node["left"], accum)
    _collect_importance(node["right"], accum)


# ---------------------------------------------------------------------------
# Decision tree
# ---------------------------------------------------------------------------

def decision_tree(features: Any, target: Iterable[Any], task: str = "regression",
                  max_depth: int | None = None, min_samples_split: int = 2,
                  min_samples_leaf: int = 1, max_features: Any = None,
                  seed: Any = 0) -> dict[str, Any]:
    """Fit a CART decision tree for regression or classification.

    Regression trees minimize squared error; classification trees minimize
    Gini impurity. ``max_features`` limits the predictors considered at each
    split (an int, a fraction, ``"sqrt"`` or ``"log2"``). A value of ``None``
    means no depth limit, capped at 100 for recursion safety.
    """
    rows = _design(features)
    n = len(rows)
    kind = _task(task)
    regression = kind == "regression"
    labels = [float(value) for value in (target or [])] if regression else list(target or [])
    if len(labels) != n:
        raise ValueError("features and target lengths must match")
    if n == 0:
        raise ValueError("target is required")
    depth_limit = 100 if max_depth is None else int(max_depth)
    if depth_limit < 1:
        raise ValueError("max_depth must be at least 1")
    split_min = int(min_samples_split)
    if split_min < 2:
        raise ValueError("min_samples_split must be at least 2")
    leaf_min = int(min_samples_leaf)
    if leaf_min < 1:
        raise ValueError("min_samples_leaf must be at least 1")
    width = len(rows[0])
    feature_count = _feature_count(max_features, width)
    classes = [] if regression else _classes(labels)
    rng = random.Random(seed)
    tree = _grow(
        rows, labels, list(range(n)), regression, classes, 0, depth_limit,
        split_min, leaf_min, feature_count, rng,
    )
    accum = [0.0] * width
    _collect_importance(tree, accum)
    total = sum(accum)
    importance = [value / total for value in accum] if total > 0.0 else accum
    return {
        "estimator": "decision_tree",
        "task": kind,
        "tree": tree,
        "classes": classes,
        "feature_importances": importance,
        "n_features": width,
        "n": n,
        "max_depth": depth_limit,
        "min_samples_split": split_min,
        "min_samples_leaf": leaf_min,
        "max_features": max_features,
        "seed": seed,
    }


def predict_tree(model: dict[str, Any], features: Any) -> dict[str, Any]:
    """Predict with a fitted decision tree."""
    rows = _design(features)
    if model.get("task") == "classification":
        classes = model["classes"]
        predicted = []
        probabilities = []
        for row in rows:
            leaf = _walk(model["tree"], row)
            predicted.append(leaf["value"])
            probabilities.append(list(leaf["probabilities"]))
        return {
            "predicted": predicted,
            "probabilities": probabilities,
            "classes": list(classes),
        }
    predicted = [float(_walk(model["tree"], row)["value"]) for row in rows]
    return {"predicted": predicted}


def tree_feature_importance(model: dict[str, Any],
                            names: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """Rank features by their accumulated split gain."""
    scores = list(model["feature_importances"])
    width = len(scores)
    if names is None:
        labels = ["x" + str(index + 1) for index in range(width)]
    else:
        labels = list(names)
        if len(labels) != width:
            raise ValueError("names length must match the number of features")
    table = [
        {"feature": labels[index], "importance": scores[index]}
        for index in range(width)
    ]
    table.sort(key=lambda entry: (-entry["importance"], entry["feature"]))
    return table


# ---------------------------------------------------------------------------
# Random forest
# ---------------------------------------------------------------------------

def random_forest(features: Any, target: Iterable[Any], task: str = "regression",
                  n_estimators: int = 100, max_depth: int | None = None,
                  min_samples_split: int = 2, min_samples_leaf: int = 1,
                  max_features: Any = "sqrt", bootstrap: bool = True,
                  seed: Any = 0) -> dict[str, Any]:
    """Fit a bagged random forest with optional out-of-bag scoring.

    Each tree is grown on a bootstrap sample (or the full sample when
    ``bootstrap`` is false) with a random subset of features at every split.
    Regression predictions average the trees; classification predictions use
    a majority vote with averaged class probabilities.
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
    width = len(rows[0])
    classes = [] if regression else _classes(labels)
    rng = random.Random(seed)
    trees = []
    importance = [0.0] * width
    oob_sum = [0.0] * n
    oob_count = [0] * n
    oob_votes = [[0.0] * len(classes) for _ in range(n)]
    for _ in range(count):
        if bootstrap:
            sample = [rng.randrange(n) for _ in range(n)]
        else:
            sample = list(range(n))
        tree = decision_tree(
            [rows[i] for i in sample],
            [labels[i] for i in sample],
            kind,
            max_depth,
            min_samples_split,
            min_samples_leaf,
            max_features,
            rng.randrange(2 ** 31),
        )
        trees.append(tree)
        for index, value in enumerate(tree["feature_importances"]):
            importance[index] += value
        if not bootstrap:
            continue
        in_bag = set(sample)
        for index in range(n):
            if index in in_bag:
                continue
            leaf = _walk(tree["tree"], rows[index])
            oob_count[index] += 1
            if regression:
                oob_sum[index] += float(leaf["value"])
            else:
                for position, label in enumerate(classes):
                    oob_votes[index][position] += leaf["probabilities"][position]
    total_importance = sum(importance)
    if total_importance > 0.0:
        importance = [value / total_importance for value in importance]

    oob_predictions: list[Any] = []
    oob_score = None
    scored = [index for index in range(n) if oob_count[index] > 0]
    if bootstrap and scored:
        if regression:
            oob_predictions = [
                oob_sum[index] / oob_count[index] if oob_count[index] else None
                for index in range(n)
            ]
            center = mean([labels[index] for index in scored])
            residual = sum(
                (labels[index] - oob_predictions[index]) ** 2 for index in scored
            )
            spread = sum((labels[index] - center) ** 2 for index in scored)
            oob_score = 1.0 - residual / spread if spread else 0.0
        else:
            for index in range(n):
                if oob_count[index] == 0:
                    oob_predictions.append(None)
                    continue
                position = max(
                    range(len(classes)),
                    key=lambda slot: (oob_votes[index][slot], -slot),
                )
                oob_predictions.append(classes[position])
            correct = sum(
                1 for index in scored
                if oob_predictions[index] == labels[index]
            )
            oob_score = correct / len(scored)

    return {
        "estimator": "random_forest",
        "task": kind,
        "trees": trees,
        "n_estimators": count,
        "classes": classes,
        "feature_importances": importance,
        "n_features": width,
        "n": n,
        "oob_score": oob_score,
        "oob_predictions": oob_predictions,
        "bootstrap": bool(bootstrap),
        "max_depth": max_depth,
        "min_samples_split": int(min_samples_split),
        "min_samples_leaf": int(min_samples_leaf),
        "max_features": max_features,
        "seed": seed,
    }


def predict_forest(model: dict[str, Any], features: Any) -> dict[str, Any]:
    """Predict with a fitted random forest."""
    rows = _design(features)
    trees = model["trees"]
    if not trees:
        raise ValueError("the forest has no trees")
    if model.get("task") == "classification":
        classes = model["classes"]
        probabilities = []
        predicted = []
        for row in rows:
            totals = [0.0] * len(classes)
            for tree in trees:
                leaf = _walk(tree["tree"], row)
                for position in range(len(classes)):
                    totals[position] += leaf["probabilities"][position]
            averaged = [value / len(trees) for value in totals]
            probabilities.append(averaged)
            position = max(
                range(len(classes)),
                key=lambda slot: (averaged[slot], -slot),
            )
            predicted.append(classes[position])
        return {
            "predicted": predicted,
            "probabilities": probabilities,
            "classes": list(classes),
        }
    predicted = []
    for row in rows:
        values = [float(_walk(tree["tree"], row)["value"]) for tree in trees]
        predicted.append(mean(values))
    return {"predicted": predicted}


def forest_feature_importance(model: dict[str, Any],
                              names: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """Rank features by their averaged forest importance."""
    return tree_feature_importance(model, names)


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_tree_namespace() -> dict[str, Any]:
    return {
        "decision_tree": decision_tree,
        "predict_tree": predict_tree,
        "tree_feature_importance": tree_feature_importance,
        "random_forest": random_forest,
        "predict_forest": predict_forest,
        "forest_feature_importance": forest_feature_importance,
    }
