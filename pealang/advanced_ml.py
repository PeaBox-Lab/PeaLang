"""Advanced machine learning algorithms for PeaLang.

Provides dependency-free implementations of common classifiers and
regressors: k-nearest neighbors, naive Bayes, and support vector machines
(linear, via sub-gradient descent).
"""

from __future__ import annotations

import math
import random
from typing import Any, Sequence


def _nums(values):
    out = []
    for v in values or []:
        if v is None or isinstance(v, bool):
            continue
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            continue
    return out


def _euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ---------------------------------------------------------------------------
# k-Nearest Neighbors
# ---------------------------------------------------------------------------

def knn_fit(X, y, k=5):
    """Fit a k-NN classifier. Returns a model dict."""
    X = [list(r) for r in X]
    y = list(y)
    return {"kind": "knn", "X": X, "y": y, "k": int(k)}


def knn_predict(model, X):
    """Predict labels for X using a fitted k-NN model."""
    Xtr = model["X"]
    ytr = model["y"]
    k = model["k"]
    preds = []
    for row in X:
        r = list(row)
        dists = sorted(range(len(Xtr)), key=lambda i: _euclidean(Xtr[i], r))
        neighbors = [ytr[i] for i in dists[:k]]
        # majority vote
        counts = {}
        for lbl in neighbors:
            counts[lbl] = counts.get(lbl, 0) + 1
        pred = max(counts, key=lambda lbl: (counts[lbl],))
        preds.append(pred)
    return preds


def knn_score(model, X, y):
    preds = knn_predict(model, X)
    correct = sum(1 for p, t in zip(preds, y) if p == t)
    return correct / len(y) if y else 0.0


# ---------------------------------------------------------------------------
# Naive Bayes (Gaussian)
# ---------------------------------------------------------------------------

def naive_bayes_fit(X, y):
    """Fit a Gaussian naive Bayes classifier."""
    classes = sorted(set(y))
    # per-class stats
    class_stats = {}
    for cls in classes:
        rows = [X[i] for i in range(len(X)) if y[i] == cls]
        n = len(rows)
        if n == 0:
            continue
        nfeat = len(X[0]) if X else 0
        means = []
        variances = []
        for j in range(nfeat):
            col = [r[j] for r in rows]
            m = sum(col) / n
            v = sum((x - m) ** 2 for x in col) / n if n > 0 else 0.0
            if v == 0:
                v = 1e-9
            means.append(m)
            variances.append(v)
        class_stats[cls] = {"count": n, "means": means, "variances": variances}
    priors = {cls: class_stats[cls]["count"] / len(y) for cls in class_stats}
    return {"kind": "naive_bayes", "classes": classes, "stats": class_stats, "priors": priors}


def _gaussian_pdf(x, mean, var):
    return (1.0 / math.sqrt(2 * math.pi * var)) * math.exp(-0.5 * (x - mean) ** 2 / var)


def naive_bayes_predict(model, X):
    classes = model["classes"]
    stats = model["stats"]
    priors = model["priors"]
    preds = []
    for row in X:
        r = list(row)
        best_cls = None
        best_log = None
        for cls in classes:
            if cls not in stats:
                continue
            s = stats[cls]
            log_prob = math.log(priors[cls] + 1e-12)
            for j, val in enumerate(r):
                m = s["means"][j]
                v = s["variances"][j]
                log_prob += math.log(_gaussian_pdf(val, m, v) + 1e-12)
            if best_log is None or log_prob > best_log:
                best_log = log_prob
                best_cls = cls
        preds.append(best_cls)
    return preds


def naive_bayes_score(model, X, y):
    preds = naive_bayes_predict(model, X)
    correct = sum(1 for p, t in zip(preds, y) if p == t)
    return correct / len(y) if y else 0.0


# ---------------------------------------------------------------------------
# Linear SVM (sub-gradient descent)
# ---------------------------------------------------------------------------

def svm_fit(X, y, C=1.0, lr=0.001, epochs=1000, seed=42):
    """Fit a linear SVM classifier using sub-gradient descent."""
    rng = random.Random(seed)
    X = [list(r) for r in X]
    y = [1 if yi > 0 else -1 for yi in y]
    n = len(X)
    d = len(X[0]) if X else 0
    w = [rng.gauss(0, 0.01) for _ in range(d)]
    b = 0.0
    for _ in range(epochs):
        for i in range(n):
            xi = X[i]
            yi = y[i]
            margin = yi * (sum(w[j] * xi[j] for j in range(d)) + b)
            if margin < 1:
                for j in range(d):
                    w[j] += lr * (C * yi * xi[j] - w[j] / n)
                b += lr * C * yi
            else:
                for j in range(d):
                    w[j] -= lr * w[j] / n
    return {"kind": "svm", "w": w, "b": b, "C": C}


def svm_predict(model, X):
    w = model["w"]
    b = model["b"]
    preds = []
    for row in X:
        r = list(row)
        val = sum(w[j] * r[j] for j in range(len(w))) + b
        preds.append(1 if val >= 0 else -1)
    return preds


def svm_score(model, X, y):
    preds = svm_predict(model, X)
    y_bin = [1 if yi > 0 else -1 for yi in y]
    correct = sum(1 for p, t in zip(preds, y_bin) if p == t)
    return correct / len(y) if y else 0.0


def build_ml_namespace() -> dict[str, Any]:
    return {
        "knn_fit": knn_fit,
        "knn_predict": knn_predict,
        "knn_score": knn_score,
        "naive_bayes_fit": naive_bayes_fit,
        "naive_bayes_predict": naive_bayes_predict,
        "naive_bayes_score": naive_bayes_score,
        "svm_fit": svm_fit,
        "svm_predict": svm_predict,
        "svm_score": svm_score,
    }
