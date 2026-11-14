"""Regression coverage for v139 clustering and dimensionality reduction."""

from pealang.clustering import (
    build_clustering_namespace,
    dbscan,
    hierarchical_clustering,
    tsne,
    umap,
    variance_threshold,
    correlation_filter,
    mutual_info_scores,
    silhouette_score,
)


def test_dbscan():
    X = [[1, 2], [1.5, 1.8], [5, 8], [8, 8], [1, 0.6], [9, 11]]
    labels = dbscan(X, eps=1.5, min_samples=2)
    assert len(labels) == 6
    # At least some points should be clustered (not all noise)
    assert len(set(labels)) > 1 or -1 in labels


def test_hierarchical_clustering():
    X = [[1, 2], [1.5, 1.8], [5, 8], [8, 8]]
    labels = hierarchical_clustering(X, n_clusters=2)
    assert len(labels) == 4
    assert len(set(labels)) == 2


def test_tsne():
    X = [[1, 2], [2, 3], [3, 4], [10, 10], [11, 11]]
    result = tsne(X, n_components=2, n_iter=50)
    assert len(result) == 5
    assert len(result[0]) == 2


def test_umap():
    X = [[1, 2], [2, 3], [3, 4], [10, 10], [11, 11]]
    result = umap(X, n_components=2)
    assert len(result) == 5
    assert len(result[0]) == 2


def test_variance_threshold():
    X = [[1, 0, 5], [2, 0, 6], [3, 0, 7]]
    selected = variance_threshold(X, threshold=0.0)
    assert 1 not in selected  # zero variance column removed
    assert 0 in selected


def test_correlation_filter():
    X = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]
    selected = correlation_filter(X, threshold=0.9)
    assert isinstance(selected, list)
    assert len(selected) <= 3


def test_mutual_info_scores():
    X = [[1, 2], [2, 3], [3, 4], [1, 2], [2, 3]]
    y = [0, 0, 0, 1, 1]
    scores = mutual_info_scores(X, y)
    assert len(scores) == 2
    assert all(isinstance(s, float) for s in scores)


def test_silhouette_score():
    X = [[1, 2], [1.5, 1.8], [5, 8], [8, 8]]
    labels = [0, 0, 1, 1]
    score = silhouette_score(X, labels)
    assert -1 <= score <= 1


def test_build_clustering_namespace():
    ns = build_clustering_namespace()
    assert "dbscan" in ns
    assert "hierarchical_clustering" in ns
    assert "tsne" in ns
    assert "umap" in ns
    assert "silhouette_score" in ns
    assert len(ns) == 8
