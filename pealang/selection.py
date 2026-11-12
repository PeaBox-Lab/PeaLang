"""Model selection: cross-validation, grid search and random search.

This module is the tuning layer above :mod:`pealang.trees` and
:mod:`pealang.boosting`. It scores tree, forest and boosting estimators with
k-fold cross-validation, then searches a parameter grid or a random sample of
it. Everything is pure Python and dependency-free.

PeaLang functions are not passed to native code as callables, so estimators are
selected by name: ``"tree"``, ``"forest"`` or ``"boosting"``.
"""

from __future__ import annotations

import itertools
import random
from typing import Any, Iterable

from .boosting import gradient_boosting, predict_boosting
from .evaluation import (accuracy_score, balanced_accuracy, k_fold, log_loss,
                         mean_absolute_error, mean_squared_error,
                         precision_recall_fscore, r2_score,
                         explained_variance_score, roc_auc,
                         root_mean_squared_error, stratified_k_fold)
from .numerics import mean, std
from .trees import (decision_tree, predict_tree, predict_forest, random_forest,
                    _design, _task)


# ---------------------------------------------------------------------------
# Estimators
# ---------------------------------------------------------------------------

_ESTIMATORS = {
    "tree": "tree",
    "decision_tree": "tree",
    "forest": "forest",
    "random_forest": "forest",
    "boosting": "boosting",
    "gradient_boosting": "boosting",
    "gbm": "boosting",
}

_PARAMETERS = {
    "tree": {"max_depth", "min_samples_split", "min_samples_leaf",
             "max_features", "seed"},
    "forest": {"n_estimators", "max_depth", "min_samples_split",
               "min_samples_leaf", "max_features", "bootstrap", "seed"},
    "boosting": {"n_estimators", "learning_rate", "max_depth",
                 "min_samples_split", "min_samples_leaf", "subsample",
                 "max_features", "seed"},
}


def _estimator_key(name: Any) -> str:
    key = str(name or "").lower()
    if key not in _ESTIMATORS:
        raise ValueError(
            "estimator must be 'tree', 'forest' or 'boosting'"
        )
    return _ESTIMATORS[key]


def _fit(estimator: str, features: Any, target: Iterable[Any], task: str,
         params: dict[str, Any]) -> dict[str, Any]:
    key = _estimator_key(estimator)
    unknown = sorted(set(params) - _PARAMETERS[key])
    if unknown:
        raise ValueError(
            "unknown parameter(s) for " + key + ": " + ", ".join(unknown)
        )
    if key == "tree":
        return decision_tree(
            features, target, task,
            params.get("max_depth"),
            params.get("min_samples_split", 2),
            params.get("min_samples_leaf", 1),
            params.get("max_features"),
            params.get("seed", 0),
        )
    if key == "forest":
        return random_forest(
            features, target, task,
            params.get("n_estimators", 100),
            params.get("max_depth"),
            params.get("min_samples_split", 2),
            params.get("min_samples_leaf", 1),
            params.get("max_features", "sqrt"),
            params.get("bootstrap", True),
            params.get("seed", 0),
        )
    return gradient_boosting(
        features, target, task,
        params.get("n_estimators", 100),
        params.get("learning_rate", 0.1),
        params.get("max_depth", 3),
        params.get("min_samples_split", 2),
        params.get("min_samples_leaf", 1),
        params.get("subsample", 1.0),
        params.get("max_features"),
        params.get("seed", 0),
    )


def _predict(estimator: str, model: dict[str, Any], features: Any) -> dict[str, Any]:
    key = _estimator_key(estimator)
    if key == "tree":
        return predict_tree(model, features)
    if key == "forest":
        return predict_forest(model, features)
    return predict_boosting(model, features)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

_REGRESSION_SCORES = {
    "r2": r2_score,
    "mse": mean_squared_error,
    "rmse": root_mean_squared_error,
    "mae": mean_absolute_error,
    "explained_variance": explained_variance_score,
}

_CLASSIFICATION_SCORES = {
    "accuracy", "balanced_accuracy", "f1", "roc_auc", "log_loss",
}

_LOWER_IS_BETTER = {"mse", "rmse", "mae", "log_loss"}

_SCORE_ALIASES = {
    "r_squared": "r2",
    "r2_score": "r2",
    "acc": "accuracy",
    "auc": "roc_auc",
    "explained": "explained_variance",
}


def _resolve_scoring(scoring: Any, task: str) -> str:
    key = str(scoring or "auto").lower()
    key = _SCORE_ALIASES.get(key, key)
    if key == "auto":
        return "r2" if task == "regression" else "accuracy"
    if task == "regression" and key not in _REGRESSION_SCORES:
        raise ValueError(
            "regression scoring must be one of: " +
            ", ".join(sorted(_REGRESSION_SCORES))
        )
    if task == "classification" and key not in _CLASSIFICATION_SCORES:
        raise ValueError(
            "classification scoring must be one of: " +
            ", ".join(sorted(_CLASSIFICATION_SCORES))
        )
    return key


def _higher_is_better(scoring: str) -> bool:
    return scoring not in _LOWER_IS_BETTER


def _score(task: str, scoring: str, actual: list[Any],
           result: dict[str, Any]) -> float:
    if task == "regression":
        return float(_REGRESSION_SCORES[scoring](actual, result["predicted"]))
    predicted = result["predicted"]
    if scoring == "accuracy":
        return float(accuracy_score(actual, predicted))
    if scoring == "balanced_accuracy":
        return float(balanced_accuracy(actual, predicted))
    if scoring == "f1":
        return float(precision_recall_fscore(actual, predicted)["f1"])
    probabilities = result.get("probabilities")
    classes = result.get("classes") or []
    if not probabilities:
        raise ValueError(scoring + " requires predicted probabilities")
    if len(classes) != 2:
        raise ValueError(scoring + " requires binary classification")
    scores = [row[1] for row in probabilities]
    if scoring == "roc_auc":
        return float(roc_auc(actual, scores, classes[1]))
    return float(log_loss(actual, scores, classes[1]))


def _fold_indices(task: str, labels: list[Any], count: int,
                  shuffle: bool, seed: Any) -> list[dict[str, Any]]:
    if task == "classification":
        try:
            return stratified_k_fold(labels, count, shuffle, seed)
        except ValueError:
            return k_fold(len(labels), count, shuffle, seed)
    return k_fold(len(labels), count, shuffle, seed)


# ---------------------------------------------------------------------------
# Cross-validation
# ---------------------------------------------------------------------------

def cross_validate(estimator: str, features: Any, target: Iterable[Any],
                   task: str = "regression", params: dict[str, Any] | None = None,
                   folds: int = 5, seed: Any = 0, scoring: Any = "auto",
                   shuffle: bool = True) -> dict[str, Any]:
    """Score an estimator with k-fold cross-validation.

    ``estimator`` is ``"tree"``, ``"forest"`` or ``"boosting"``. ``params`` is
    a dict of estimator settings. Classification uses stratified folds when
    every class has at least ``folds`` samples and falls back to plain k-fold
    otherwise. Returns the per-fold scores, their mean and standard deviation.
    """
    rows = _design(features)
    labels = list(target or [])
    n = len(rows)
    if len(labels) != n:
        raise ValueError("features and target lengths must match")
    kind = _task(task)
    count = int(folds)
    if count < 2:
        raise ValueError("folds must be at least 2")
    if count > n:
        raise ValueError("folds cannot exceed the number of samples")
    settings = dict(params or {})
    name = _resolve_scoring(scoring, kind)
    fold_list = _fold_indices(kind, labels, count, shuffle, seed)
    scores: list[float] = []
    for fold in fold_list:
        train_rows = [rows[index] for index in fold["train"]]
        train_target = [labels[index] for index in fold["train"]]
        test_rows = [rows[index] for index in fold["test"]]
        test_target = [labels[index] for index in fold["test"]]
        model = _fit(estimator, train_rows, train_target, kind, settings)
        result = _predict(estimator, model, test_rows)
        scores.append(_score(kind, name, test_target, result))
    return {
        "estimator": _estimator_key(estimator),
        "task": kind,
        "scoring": name,
        "params": settings,
        "scores": scores,
        "mean": float(mean(scores)),
        "std": float(std(scores, True) or 0.0),
        "folds": len(fold_list),
        "higher_is_better": _higher_is_better(name),
        "seed": seed,
    }


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def _validate_grid(param_grid: Any) -> dict[str, list[Any]]:
    if param_grid is None:
        return {}
    if not isinstance(param_grid, dict):
        raise ValueError("param_grid must be a dict of parameter lists")
    grid: dict[str, list[Any]] = {}
    for key, values in param_grid.items():
        if isinstance(values, (str, bytes)) or not isinstance(values, (list, tuple)):
            raise ValueError("param_grid values must be lists")
        if not values:
            raise ValueError("param_grid values must not be empty")
        grid[str(key)] = list(values)
    return grid


def _combinations(grid: dict[str, list[Any]]) -> tuple[list[str], list[tuple[Any, ...]]]:
    keys = sorted(grid)
    if not keys:
        return keys, [()]
    return keys, list(itertools.product(*[grid[key] for key in keys]))


def _evaluate_candidates(estimator: str, rows: list[list[float]],
                         labels: list[Any], task: str, keys: list[str],
                         combinations: list[tuple[Any, ...]], folds: int,
                         seed: Any, scoring: Any,
                         shuffle: bool) -> tuple[list[dict[str, Any]],
                                                 dict[str, Any], str, bool]:
    name = _resolve_scoring(scoring, task)
    higher = _higher_is_better(name)
    results: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for combination in combinations:
        params = dict(zip(keys, combination))
        report = cross_validate(
            estimator, rows, labels, task, params, folds, seed, name, shuffle
        )
        entry = {
            "params": params,
            "mean": report["mean"],
            "std": report["std"],
            "scores": report["scores"],
        }
        results.append(entry)
        if best is None or (
            entry["mean"] > best["mean"] if higher else entry["mean"] < best["mean"]
        ):
            best = entry
    ordered = sorted(
        results, key=lambda entry: -entry["mean"] if higher else entry["mean"]
    )
    return ordered, best, name, higher


def _search_result(estimator: str, rows: list[list[float]], labels: list[Any],
                   task: str, ordered: list[dict[str, Any]],
                   best: dict[str, Any], name: str, higher: bool,
                   folds: int, seed: Any) -> dict[str, Any]:
    model = _fit(estimator, rows, labels, task, best["params"])
    return {
        "estimator": _estimator_key(estimator),
        "task": task,
        "scoring": name,
        "best_params": best["params"],
        "best_score": best["mean"],
        "best_std": best["std"],
        "best_model": model,
        "results": ordered,
        "n_candidates": len(ordered),
        "folds": folds,
        "seed": seed,
        "higher_is_better": higher,
    }


def grid_search(estimator: str, features: Any, target: Iterable[Any],
                task: str = "regression", param_grid: dict[str, Any] | None = None,
                folds: int = 5, seed: Any = 0, scoring: Any = "auto",
                shuffle: bool = True) -> dict[str, Any]:
    """Exhaustively score every parameter combination and refit the best one.

    ``param_grid`` maps parameter names to lists of candidate values. The
    result contains the ranked ``results``, the ``best_params`` and a
    ``best_model`` fitted on all rows.
    """
    rows = _design(features)
    labels = list(target or [])
    n = len(rows)
    if len(labels) != n:
        raise ValueError("features and target lengths must match")
    kind = _task(task)
    count = int(folds)
    if count < 2:
        raise ValueError("folds must be at least 2")
    if count > n:
        raise ValueError("folds cannot exceed the number of samples")
    grid = _validate_grid(param_grid)
    keys, combinations = _combinations(grid)
    ordered, best, name, higher = _evaluate_candidates(
        estimator, rows, labels, kind, keys, combinations, count, seed,
        scoring, shuffle,
    )
    return _search_result(
        estimator, rows, labels, kind, ordered, best, name, higher, count, seed
    )


def random_search(estimator: str, features: Any, target: Iterable[Any],
                  task: str = "regression",
                  param_grid: dict[str, Any] | None = None,
                  n_iter: int = 10, folds: int = 5, seed: Any = 0,
                  scoring: Any = "auto",
                  shuffle: bool = True) -> dict[str, Any]:
    """Score a random sample of the parameter grid and refit the best one.

    ``n_iter`` is the number of candidates to evaluate. Sampling is seeded, so
    the same seed produces the same candidates.
    """
    rows = _design(features)
    labels = list(target or [])
    n = len(rows)
    if len(labels) != n:
        raise ValueError("features and target lengths must match")
    kind = _task(task)
    count = int(folds)
    if count < 2:
        raise ValueError("folds must be at least 2")
    if count > n:
        raise ValueError("folds cannot exceed the number of samples")
    iterations = int(n_iter)
    if iterations < 1:
        raise ValueError("n_iter must be at least 1")
    grid = _validate_grid(param_grid)
    keys = sorted(grid)
    rng = random.Random(seed)
    combinations: list[tuple[Any, ...]] = []
    if not keys:
        combinations = [()] * iterations
    else:
        seen: set[str] = set()
        attempts = 0
        limit = max(iterations * 20, 100)
        while len(combinations) < iterations and attempts < limit:
            candidate = tuple(rng.choice(grid[key]) for key in keys)
            marker = repr(candidate)
            attempts += 1
            if marker in seen:
                continue
            seen.add(marker)
            combinations.append(candidate)
        while len(combinations) < iterations:
            combinations.append(tuple(rng.choice(grid[key]) for key in keys))
    ordered, best, name, higher = _evaluate_candidates(
        estimator, rows, labels, kind, keys, combinations, count, seed,
        scoring, shuffle,
    )
    return _search_result(
        estimator, rows, labels, kind, ordered, best, name, higher, count, seed
    )


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_selection_namespace() -> dict[str, Any]:
    return {
        "cross_validate": cross_validate,
        "grid_search": grid_search,
        "random_search": random_search,
    }
