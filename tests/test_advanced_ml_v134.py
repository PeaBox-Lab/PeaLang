"""Regression coverage for v134 advanced ML."""

from pealang.advanced_ml import (
    build_ml_namespace,
    knn_fit, knn_predict, knn_score,
    naive_bayes_fit, naive_bayes_predict, naive_bayes_score,
    svm_fit, svm_predict, svm_score,
)


def test_knn():
    X = [[1, 2], [2, 3], [3, 4], [10, 10], [11, 11]]
    y = [0, 0, 0, 1, 1]
    model = knn_fit(X, y, k=3)
    preds = knn_predict(model, [[2, 3], [10, 10]])
    assert preds == [0, 1]
    score = knn_score(model, [[2, 3], [10, 10]], [0, 1])
    assert score == 1.0


def test_naive_bayes():
    X = [[1, 2], [2, 3], [3, 4], [10, 10], [11, 11], [12, 12]]
    y = [0, 0, 0, 1, 1, 1]
    model = naive_bayes_fit(X, y)
    preds = naive_bayes_predict(model, [[2, 3], [11, 11]])
    assert preds == [0, 1]
    score = naive_bayes_score(model, [[2, 3], [11, 11]], [0, 1])
    assert score == 1.0


def test_svm():
    X = [[1, 2], [2, 3], [3, 4], [-1, -2], [-2, -3], [-3, -4]]
    y = [1, 1, 1, -1, -1, -1]
    model = svm_fit(X, y, epochs=500)
    preds = svm_predict(model, [[2, 3], [-2, -3]])
    assert preds[0] == 1
    assert preds[1] == -1
    score = svm_score(model, X, y)
    assert score >= 0.8


def test_build_ml_namespace():
    ns = build_ml_namespace()
    assert "knn_fit" in ns
    assert "naive_bayes_fit" in ns
    assert "svm_fit" in ns
    assert len(ns) == 9
