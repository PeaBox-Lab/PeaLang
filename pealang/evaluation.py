"""Model evaluation, resampling and feature preparation.

This module is the assessment layer above :mod:`pealang.modeling`. It provides
train/test splitting, k-fold and stratified k-fold index generators,
classification and regression metrics, ROC/AUC, calibration, and feature
encoders and transforms. Everything is pure Python and dependency-free.
"""

from __future__ import annotations

import math
import random
from itertools import combinations_with_replacement
from typing import Any, Iterable, Sequence

from .numerics import mean, std, variance


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _numbers(values: Iterable[Any], name: str = "values") -> list[float]:
    out: list[float] = []
    for value in values or []:
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            raise ValueError(name + " must be numeric") from None
    return out


def _items(values: Iterable[Any]) -> list[Any]:
    return list(values or [])


def _same_length(*sequences: Sequence[Any]) -> int:
    if not sequences:
        return 0
    n = len(sequences[0])
    for sequence in sequences[1:]:
        if len(sequence) != n:
            raise ValueError("input lengths must match")
    return n


def _matrix(features: Any) -> list[list[float]]:
    rows = [[float(value) for value in row] for row in (features or [])]
    if not rows:
        raise ValueError("features are required")
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise ValueError("feature rows must be non-empty and equal length")
    return rows


def _unique(values: Iterable[Any]) -> list[Any]:
    out: list[Any] = []
    for value in values:
        if value not in out:
            out.append(value)
    return out


def _key(value: Any) -> Any:
    try:
        hash(value)
    except TypeError:
        return repr(value)
    return value


def _resolve_positive(labels: Sequence[Any], positive: Any) -> Any:
    if positive is not None:
        if positive not in labels:
            raise ValueError("positive label is not present in the data")
        return positive
    ordered = sorted(labels, key=lambda value: (str(type(value)), repr(value)))
    if len(ordered) != 2:
        raise ValueError("a positive label is required for multiclass data")
    return ordered[-1]


# ---------------------------------------------------------------------------
# Resampling
# ---------------------------------------------------------------------------

def train_test_split(features: Any, target: Iterable[Any], test_size: float = 0.25,
                     shuffle: bool = True, seed: Any = None,
                     stratify: Iterable[Any] | None = None) -> dict[str, Any]:
    """Split features and target into train and test subsets.

    ``test_size`` is the fraction of rows placed in the test set. ``stratify``
    accepts one label per row and keeps the class proportions in both splits.
    Returns the split arrays plus the original row indices.
    """
    rows = _items(features)
    y = _items(target)
    n = _same_length(rows, y)
    if n == 0:
        raise ValueError("features are required")
    fraction = float(test_size)
    if not 0.0 < fraction < 1.0:
        raise ValueError("test_size must be between 0 and 1")
    n_test = max(1, min(n - 1, int(math.ceil(n * fraction))))
    rng = random.Random(seed)

    if stratify is not None:
        strata = _items(stratify)
        if len(strata) != n:
            raise ValueError("stratify length must match features")
        groups: dict[Any, list[int]] = {}
        order: list[Any] = []
        for index, label in enumerate(strata):
            key = _key(label)
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(index)

        # Allocate test slots across strata by largest remainder, keeping at
        # least one test row in every stratum that has two or more rows.
        quotas: list[list[Any]] = []
        for key in order:
            members = groups[key]
            exact = len(members) * fraction
            count = int(math.floor(exact))
            count = min(count, len(members) - 1) if len(members) >= 2 else 0
            if len(members) >= 2 and count == 0:
                count = 1
            quotas.append([key, count, exact - math.floor(exact), len(members)])
        allocated = sum(item[1] for item in quotas)
        if allocated < n_test:
            for item in sorted(quotas, key=lambda entry: -entry[2]):
                if allocated >= n_test:
                    break
                if item[1] < item[3] - 1:
                    item[1] += 1
                    allocated += 1
            moved = True
            while allocated < n_test and moved:
                moved = False
                for item in quotas:
                    if allocated >= n_test:
                        break
                    if item[1] < item[3] - 1:
                        item[1] += 1
                        allocated += 1
                        moved = True
        elif allocated > n_test:
            for item in sorted(quotas, key=lambda entry: entry[2]):
                if allocated <= n_test:
                    break
                floor_count = 1 if item[3] >= 2 else 0
                if item[1] > floor_count:
                    item[1] -= 1
                    allocated -= 1

        chosen: list[int] = []
        for key, count, _, _ in quotas:
            members = groups[key]
            if shuffle:
                rng.shuffle(members)
            chosen.extend(members[:count])
        test_set = set(chosen)
    else:
        index = list(range(n))
        if shuffle:
            rng.shuffle(index)
        test_set = set(index[:n_test])

    train_index = [index for index in range(n) if index not in test_set]
    test_index = sorted(test_set)
    return {
        "X_train": [rows[index] for index in train_index],
        "X_test": [rows[index] for index in test_index],
        "y_train": [y[index] for index in train_index],
        "y_test": [y[index] for index in test_index],
        "train_index": train_index,
        "test_index": test_index,
        "n_train": len(train_index),
        "n_test": len(test_index),
        "stratified": stratify is not None,
    }


def k_fold(samples: Any, k: int = 5, shuffle: bool = True,
           seed: Any = None) -> list[dict[str, Any]]:
    """Generate k-fold train/test index sets.

    ``samples`` is either a row count or the feature list itself. Each returned
    fold contains disjoint ``train`` and ``test`` index lists that cover every
    row exactly once in the test positions.
    """
    if isinstance(samples, bool):
        raise ValueError("samples must be a count or a list of rows")
    if isinstance(samples, int):
        n = samples
    else:
        n = len(_items(samples))
    folds_count = int(k)
    if folds_count < 2:
        raise ValueError("k must be at least 2")
    if n < folds_count:
        raise ValueError("k cannot exceed the number of samples")
    index = list(range(n))
    if shuffle:
        random.Random(seed).shuffle(index)
    base, extra = divmod(n, folds_count)
    folds: list[dict[str, Any]] = []
    start = 0
    for fold in range(folds_count):
        size = base + (1 if fold < extra else 0)
        test = index[start:start + size]
        start += size
        test_set = set(test)
        train = [row for row in range(n) if row not in test_set]
        folds.append({
            "fold": fold,
            "train": train,
            "test": test,
            "n_train": len(train),
            "n_test": len(test),
        })
    return folds


def stratified_k_fold(labels: Iterable[Any], k: int = 5, shuffle: bool = True,
                      seed: Any = None) -> list[dict[str, Any]]:
    """Generate class-balanced k-fold train/test index sets."""
    y = _items(labels)
    n = len(y)
    folds_count = int(k)
    if folds_count < 2:
        raise ValueError("k must be at least 2")
    if n < folds_count:
        raise ValueError("k cannot exceed the number of samples")
    groups: dict[Any, list[int]] = {}
    order: list[Any] = []
    for index, label in enumerate(y):
        key = _key(label)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(index)
    if any(len(members) < folds_count for members in groups.values()):
        raise ValueError("each class needs at least k samples for stratification")
    rng = random.Random(seed)
    buckets: list[list[int]] = [[] for _ in range(folds_count)]
    for key in sorted(order, key=lambda item: -len(groups[item])):
        members = groups[key]
        if shuffle:
            rng.shuffle(members)
        for index in members:
            target = min(range(folds_count), key=lambda fold: len(buckets[fold]))
            buckets[target].append(index)
    folds: list[dict[str, Any]] = []
    for fold in range(folds_count):
        test = sorted(buckets[fold])
        test_set = set(test)
        train = [index for index in range(n) if index not in test_set]
        folds.append({
            "fold": fold,
            "train": train,
            "test": test,
            "n_train": len(train),
            "n_test": len(test),
        })
    return folds


# ---------------------------------------------------------------------------
# Classification metrics
# ---------------------------------------------------------------------------

def accuracy_score(actual: Iterable[Any], predicted: Iterable[Any]) -> float:
    """Fraction of predictions that exactly match the actual label."""
    a = _items(actual)
    p = _items(predicted)
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and predicted values are required")
    return sum(1 for i in range(n) if a[i] == p[i]) / n


def balanced_accuracy(actual: Iterable[Any], predicted: Iterable[Any]) -> float:
    """Mean per-class recall, which corrects for class imbalance."""
    a = _items(actual)
    p = _items(predicted)
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and predicted values are required")
    labels = _unique(a)
    recalls = []
    for label in labels:
        positives = [i for i in range(n) if a[i] == label]
        if not positives:
            continue
        recalls.append(
            sum(1 for i in positives if p[i] == label) / len(positives)
        )
    return mean(recalls)


def precision_recall_fscore(actual: Iterable[Any], predicted: Iterable[Any],
                            positive: Any = None) -> dict[str, Any]:
    """Precision, recall, F1 and support for each class.

    Top-level ``precision``, ``recall`` and ``f1`` refer to the positive class
    for binary data and to the macro average for multiclass data. Per-class
    entries and macro, weighted and micro summaries are always included.
    """
    a = _items(actual)
    p = _items(predicted)
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and predicted values are required")
    labels = _unique(a + p)
    per_class = []
    for label in labels:
        tp = sum(1 for i in range(n) if a[i] == label and p[i] == label)
        fp = sum(1 for i in range(n) if a[i] != label and p[i] == label)
        fn = sum(1 for i in range(n) if a[i] == label and p[i] != label)
        support = sum(1 for i in range(n) if a[i] == label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append({
            "label": label,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        })
    total = sum(entry["support"] for entry in per_class)
    macro_precision = mean([entry["precision"] for entry in per_class])
    macro_recall = mean([entry["recall"] for entry in per_class])
    macro_f1 = mean([entry["f1"] for entry in per_class])
    if total:
        weighted_precision = sum(entry["precision"] * entry["support"] for entry in per_class) / total
        weighted_recall = sum(entry["recall"] * entry["support"] for entry in per_class) / total
        weighted_f1 = sum(entry["f1"] * entry["support"] for entry in per_class) / total
    else:
        weighted_precision = weighted_recall = weighted_f1 = 0.0
    correct = sum(1 for i in range(n) if a[i] == p[i])
    micro_precision = micro_recall = micro_f1 = correct / n
    if len(labels) == 2:
        chosen = _resolve_positive(labels, positive)
        entry = next(item for item in per_class if item["label"] == chosen)
        precision, recall, f1 = entry["precision"], entry["recall"], entry["f1"]
    else:
        chosen = None
        precision, recall, f1 = macro_precision, macro_recall, macro_f1
    return {
        "labels": labels,
        "per_class": per_class,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "support": total,
        "accuracy": correct / n,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "weighted_precision": weighted_precision,
        "weighted_recall": weighted_recall,
        "weighted_f1": weighted_f1,
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_f1,
        "positive": chosen,
    }


def roc_curve(actual: Iterable[Any], scores: Iterable[Any],
              positive: Any = None) -> dict[str, Any]:
    """False-positive and true-positive rates at each distinct score."""
    a = _items(actual)
    s = _numbers(scores, "scores")
    n = _same_length(a, s)
    labels = _unique(a)
    if len(labels) != 2:
        raise ValueError("roc_curve requires binary labels")
    chosen = _resolve_positive(labels, positive)
    positives = sum(1 for label in a if label == chosen)
    negatives = n - positives
    if positives == 0 or negatives == 0:
        raise ValueError("both classes are required")
    thresholds = sorted(set(s), reverse=True)
    fpr: list[float] = []
    tpr: list[float] = []
    for threshold in thresholds:
        tp = sum(1 for i in range(n) if s[i] >= threshold and a[i] == chosen)
        fp = sum(1 for i in range(n) if s[i] >= threshold and a[i] != chosen)
        tpr.append(tp / positives)
        fpr.append(fp / negatives)
    return {
        "fpr": fpr,
        "tpr": tpr,
        "thresholds": thresholds,
        "auc": _rank_auc(a, s, chosen),
        "positive": chosen,
        "n_positives": positives,
        "n_negatives": negatives,
    }


def _rank_auc(actual: Sequence[Any], scores: Sequence[float], positive: Any) -> float:
    paired = sorted(
        [(scores[i], 1 if actual[i] == positive else 0) for i in range(len(actual))],
        key=lambda item: item[0],
    )
    ranks = [0.0] * len(paired)
    index = 0
    while index < len(paired):
        end = index
        while end + 1 < len(paired) and paired[end + 1][0] == paired[index][0]:
            end += 1
        average = (index + end + 2) / 2.0
        for position in range(index, end + 1):
            ranks[position] = average
        index = end + 1
    positives = sum(1 for item in paired if item[1] == 1)
    negatives = len(paired) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("both classes are required")
    rank_sum = sum(ranks[i] for i in range(len(paired)) if paired[i][1] == 1)
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def roc_auc(actual: Iterable[Any], scores: Iterable[Any],
            positive: Any = None) -> float:
    """Area under the ROC curve, with tie-aware rank handling."""
    a = _items(actual)
    s = _numbers(scores, "scores")
    _same_length(a, s)
    labels = _unique(a)
    if len(labels) != 2:
        raise ValueError("roc_auc requires binary labels")
    return _rank_auc(a, s, _resolve_positive(labels, positive))


def log_loss(actual: Iterable[Any], probabilities: Iterable[Any],
             positive: Any = None, epsilon: float = 1e-15) -> float:
    """Binary cross-entropy for predicted probabilities of the positive class."""
    a = _items(actual)
    p = _numbers(probabilities, "probabilities")
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and probabilities are required")
    labels = _unique(a)
    if len(labels) != 2:
        raise ValueError("log_loss requires binary labels")
    chosen = _resolve_positive(labels, positive)
    eps = float(epsilon)
    if not 0.0 <= eps < 0.5:
        raise ValueError("epsilon must be between 0 and 0.5")
    total = 0.0
    for i in range(n):
        q = min(max(p[i], eps), 1.0 - eps)
        probability = q if a[i] == chosen else 1.0 - q
        total -= math.log(probability)
    return total / n


def brier_score(actual: Iterable[Any], probabilities: Iterable[Any],
                positive: Any = None) -> float:
    """Mean squared error between predicted probabilities and binary outcomes."""
    a = _items(actual)
    p = _numbers(probabilities, "probabilities")
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and probabilities are required")
    labels = _unique(a)
    if len(labels) != 2:
        raise ValueError("brier_score requires binary labels")
    chosen = _resolve_positive(labels, positive)
    return mean([(p[i] - (1.0 if a[i] == chosen else 0.0)) ** 2 for i in range(n)])


def calibration_curve(actual: Iterable[Any], probabilities: Iterable[Any],
                      bins: int = 10, positive: Any = None) -> dict[str, Any]:
    """Observed positive rate against mean predicted probability per bin."""
    a = _items(actual)
    p = _numbers(probabilities, "probabilities")
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and probabilities are required")
    labels = _unique(a)
    if len(labels) != 2:
        raise ValueError("calibration_curve requires binary labels")
    chosen = _resolve_positive(labels, positive)
    count = int(bins)
    if count < 1:
        raise ValueError("bins must be positive")
    if any(value < 0.0 or value > 1.0 for value in p):
        raise ValueError("probabilities must be between 0 and 1")
    edges = [index / count for index in range(count + 1)]
    table = []
    for bucket in range(count):
        low = edges[bucket]
        high = edges[bucket + 1]
        members = [
            index for index in range(n)
            if low <= p[index] < high or (bucket == count - 1 and p[index] == high)
        ]
        if not members:
            table.append({
                "bin_lower": low,
                "bin_upper": high,
                "count": 0,
                "mean_predicted": None,
                "fraction_positive": None,
            })
            continue
        table.append({
            "bin_lower": low,
            "bin_upper": high,
            "count": len(members),
            "mean_predicted": mean([p[index] for index in members]),
            "fraction_positive": mean([
                1.0 if a[index] == chosen else 0.0 for index in members
            ]),
        })
    return {"table": table, "bins": count, "positive": chosen, "n": n}


# ---------------------------------------------------------------------------
# Regression metrics
# ---------------------------------------------------------------------------

def mean_squared_error(actual: Iterable[Any], predicted: Iterable[Any]) -> float:
    """Mean of the squared prediction errors."""
    a = _numbers(actual, "actual")
    p = _numbers(predicted, "predicted")
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and predicted values are required")
    return sum((a[i] - p[i]) ** 2 for i in range(n)) / n


def root_mean_squared_error(actual: Iterable[Any], predicted: Iterable[Any]) -> float:
    """Square root of the mean squared error, in the target's units."""
    return math.sqrt(mean_squared_error(actual, predicted))


def mean_absolute_error(actual: Iterable[Any], predicted: Iterable[Any]) -> float:
    """Mean of the absolute prediction errors."""
    a = _numbers(actual, "actual")
    p = _numbers(predicted, "predicted")
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and predicted values are required")
    return sum(abs(a[i] - p[i]) for i in range(n)) / n


def median_absolute_error(actual: Iterable[Any], predicted: Iterable[Any]) -> float:
    """Median of the absolute prediction errors."""
    a = _numbers(actual, "actual")
    p = _numbers(predicted, "predicted")
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and predicted values are required")
    errors = sorted(abs(a[i] - p[i]) for i in range(n))
    middle = n // 2
    if n % 2:
        return errors[middle]
    return (errors[middle - 1] + errors[middle]) / 2.0


def mean_absolute_percentage_error(actual: Iterable[Any],
                                   predicted: Iterable[Any]) -> float:
    """Mean absolute percentage error as a fraction (0.1 means 10%)."""
    a = _numbers(actual, "actual")
    p = _numbers(predicted, "predicted")
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and predicted values are required")
    if any(value == 0.0 for value in a):
        raise ValueError("actual values must be non-zero for percentage error")
    return sum(abs((a[i] - p[i]) / a[i]) for i in range(n)) / n


def r2_score(actual: Iterable[Any], predicted: Iterable[Any]) -> float:
    """Coefficient of determination, 1 minus the residual variance share."""
    a = _numbers(actual, "actual")
    p = _numbers(predicted, "predicted")
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and predicted values are required")
    center = mean(a)
    ss_res = sum((a[i] - p[i]) ** 2 for i in range(n))
    ss_tot = sum((value - center) ** 2 for value in a)
    if ss_tot == 0.0:
        return 1.0 if ss_res == 0.0 else 0.0
    return 1.0 - ss_res / ss_tot


def explained_variance_score(actual: Iterable[Any],
                             predicted: Iterable[Any]) -> float:
    """Share of target variance explained by the predictions."""
    a = _numbers(actual, "actual")
    p = _numbers(predicted, "predicted")
    n = _same_length(a, p)
    if n == 0:
        raise ValueError("actual and predicted values are required")
    differences = [a[i] - p[i] for i in range(n)]
    total = variance(a)
    residual = variance(differences)
    if not total:
        return 1.0 if not residual else 0.0
    return 1.0 - residual / total


# ---------------------------------------------------------------------------
# Feature preparation
# ---------------------------------------------------------------------------

def polynomial_features(features: Any, degree: int = 2, include_bias: bool = False,
                        interaction_only: bool = False,
                        names: Sequence[str] | None = None) -> dict[str, Any]:
    """Expand features into monomials up to ``degree``.

    ``interaction_only`` keeps products of distinct features and drops pure
    powers. ``names`` labels the input columns; generated names are returned in
    ``names``.
    """
    rows = _matrix(features)
    width = len(rows[0])
    order = int(degree)
    if order < 1:
        raise ValueError("degree must be at least 1")
    if names is None:
        labels = ["x" + str(index + 1) for index in range(width)]
    else:
        labels = list(names)
        if len(labels) != width:
            raise ValueError("names length must match the number of features")
    combinations: list[tuple[int, ...]] = []
    if include_bias:
        combinations.append(())
    for power in range(1, order + 1):
        for combination in combinations_with_replacement(range(width), power):
            if interaction_only and len(set(combination)) != len(combination):
                continue
            combinations.append(combination)

    def _label(combination: tuple[int, ...]) -> str:
        counts: dict[int, int] = {}
        for index in combination:
            counts[index] = counts.get(index, 0) + 1
        parts = []
        for index in range(width):
            if index in counts:
                parts.append(
                    labels[index] if counts[index] == 1
                    else labels[index] + "^" + str(counts[index])
                )
        return "*".join(parts) if parts else "1"

    expanded = []
    for row in rows:
        values = []
        for combination in combinations:
            product = 1.0
            for index in combination:
                product *= row[index]
            values.append(product)
        expanded.append(values)
    return {
        "features": expanded,
        "names": [_label(combination) for combination in combinations],
        "input_names": labels,
        "degree": order,
        "include_bias": bool(include_bias),
        "interaction_only": bool(interaction_only),
    }


def label_encode(values: Iterable[Any]) -> dict[str, Any]:
    """Map each distinct value to a stable integer code."""
    items = _items(values)
    if not items:
        raise ValueError("values are required")
    classes = _unique(items)
    return {
        "codes": [classes.index(value) for value in items],
        "classes": classes,
        "mapping": {str(value): index for index, value in enumerate(classes)},
        "n_classes": len(classes),
    }


def ordinal_encode(values: Iterable[Any], order: Iterable[Any] | None = None) -> dict[str, Any]:
    """Map values to integer codes using an explicit or sorted order."""
    items = _items(values)
    if not items:
        raise ValueError("values are required")
    if order is None:
        classes = sorted(_unique(items), key=lambda value: (str(type(value)), repr(value)))
    else:
        classes = _items(order)
        if not classes:
            raise ValueError("order must not be empty")
    codes = []
    for value in items:
        if value not in classes:
            raise ValueError("value is not present in the ordinal order: " + repr(value))
        codes.append(classes.index(value))
    return {
        "codes": codes,
        "classes": classes,
        "mapping": {str(value): index for index, value in enumerate(classes)},
    }


def standardize_features(features: Any, sample: bool = True) -> dict[str, Any]:
    """Center each column and scale it to unit standard deviation."""
    rows = _matrix(features)
    width = len(rows[0])
    means = [mean([row[index] for row in rows]) for index in range(width)]
    deviations = [std([row[index] for row in rows], sample) or 0.0 for index in range(width)]
    scales = [value if value > 0.0 else 1.0 for value in deviations]
    transformed = [
        [(row[index] - means[index]) / scales[index] for index in range(width)]
        for row in rows
    ]
    return {
        "features": transformed,
        "means": means,
        "stds": deviations,
        "scales": scales,
        "sample": bool(sample),
    }


def standardize_transform(features: Any, means: Iterable[Any],
                          scales: Iterable[Any]) -> list[list[float]]:
    """Apply previously learned centering and scaling to new features."""
    rows = _matrix(features)
    centers = _numbers(means, "means")
    divisors = _numbers(scales, "scales")
    width = len(rows[0])
    if len(centers) != width or len(divisors) != width:
        raise ValueError("means and scales must match the number of features")
    safe = [value if value != 0.0 else 1.0 for value in divisors]
    return [
        [(row[index] - centers[index]) / safe[index] for index in range(width)]
        for row in rows
    ]


def minmax_features(features: Any) -> dict[str, Any]:
    """Scale each column into the closed interval from zero to one."""
    rows = _matrix(features)
    width = len(rows[0])
    mins = [min(row[index] for row in rows) for index in range(width)]
    maxs = [max(row[index] for row in rows) for index in range(width)]
    ranges = [(maxs[index] - mins[index]) or 1.0 for index in range(width)]
    transformed = [
        [(row[index] - mins[index]) / ranges[index] for index in range(width)]
        for row in rows
    ]
    return {
        "features": transformed,
        "mins": mins,
        "maxs": maxs,
        "ranges": ranges,
    }


def minmax_transform(features: Any, mins: Iterable[Any],
                     ranges: Iterable[Any]) -> list[list[float]]:
    """Apply previously learned min-max scaling to new features."""
    rows = _matrix(features)
    offsets = _numbers(mins, "mins")
    spans = _numbers(ranges, "ranges")
    width = len(rows[0])
    if len(offsets) != width or len(spans) != width:
        raise ValueError("mins and ranges must match the number of features")
    safe = [value if value != 0.0 else 1.0 for value in spans]
    return [
        [(row[index] - offsets[index]) / safe[index] for index in range(width)]
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------

def build_evaluation_namespace() -> dict[str, Any]:
    return {
        "train_test_split": train_test_split,
        "k_fold": k_fold,
        "stratified_k_fold": stratified_k_fold,
        "accuracy_score": accuracy_score,
        "balanced_accuracy": balanced_accuracy,
        "precision_recall_fscore": precision_recall_fscore,
        "roc_curve": roc_curve,
        "roc_auc": roc_auc,
        "log_loss": log_loss,
        "brier_score": brier_score,
        "calibration_curve": calibration_curve,
        "mean_squared_error": mean_squared_error,
        "root_mean_squared_error": root_mean_squared_error,
        "mean_absolute_error": mean_absolute_error,
        "median_absolute_error": median_absolute_error,
        "mean_absolute_percentage_error": mean_absolute_percentage_error,
        "r2_score": r2_score,
        "explained_variance_score": explained_variance_score,
        "polynomial_features": polynomial_features,
        "label_encode": label_encode,
        "ordinal_encode": ordinal_encode,
        "standardize_features": standardize_features,
        "standardize_transform": standardize_transform,
        "minmax_features": minmax_features,
        "minmax_transform": minmax_transform,
    }
