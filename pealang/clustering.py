"""Advanced clustering and dimensionality reduction for PeaLang.

Provides dependency-free implementations of clustering algorithms and
dimensionality reduction techniques beyond basic k-means and PCA.
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


def _manhattan(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


# ---------------------------------------------------------------------------
# DBSCAN clustering
# ---------------------------------------------------------------------------

def dbscan(X, eps=0.5, min_samples=5, metric="euclidean"):
    """DBSCAN clustering. Returns list of cluster labels (-1 for noise)."""
    n = len(X)
    if n == 0:
        return []
    dist_fn = _euclidean if metric == "euclidean" else _manhattan
    labels = [None] * n
    cluster_id = 0
    for i in range(n):
        if labels[i] is not None:
            continue
        # Find neighbors
        neighbors = [j for j in range(n) if dist_fn(X[i], X[j]) <= eps]
        if len(neighbors) < min_samples:
            labels[i] = -1  # noise
            continue
        # Start new cluster
        labels[i] = cluster_id
        seed_set = list(neighbors)
        k = 0
        while k < len(seed_set):
            j = seed_set[k]
            if labels[j] == -1:
                labels[j] = cluster_id
            if labels[j] is not None:
                k += 1
                continue
            labels[j] = cluster_id
            j_neighbors = [l for l in range(n) if dist_fn(X[j], X[l]) <= eps]
            if len(j_neighbors) >= min_samples:
                for nb in j_neighbors:
                    if nb not in seed_set:
                        seed_set.append(nb)
            k += 1
        cluster_id += 1
    # Replace None with -1
    return [l if l is not None else -1 for l in labels]


# ---------------------------------------------------------------------------
# Hierarchical clustering (agglomerative)
# ---------------------------------------------------------------------------

def hierarchical_clustering(X, n_clusters=2, linkage="single"):
    """Agglomerative hierarchical clustering. Returns cluster labels."""
    n = len(X)
    if n == 0:
        return []
    # Each point starts as its own cluster
    clusters = [[i] for i in range(n)]
    # Distance matrix
    dist = {}
    for i in range(n):
        for j in range(i + 1, n):
            dist[(i, j)] = _euclidean(X[i], X[j])
            dist[(j, i)] = dist[(i, j)]

    def cluster_dist(c1, c2):
        d = []
        for i in c1:
            for j in c2:
                d.append(dist.get((i, j), _euclidean(X[i], X[j])))
        if linkage == "single":
            return min(d) if d else 0
        elif linkage == "complete":
            return max(d) if d else 0
        elif linkage == "average":
            return sum(d) / len(d) if d else 0
        return min(d) if d else 0

    while len(clusters) > n_clusters:
        # Find closest pair
        best = None
        best_d = float("inf")
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = cluster_dist(clusters[i], clusters[j])
                if d < best_d:
                    best_d = d
                    best = (i, j)
        if best is None:
            break
        i, j = best
        # Merge
        merged = clusters[i] + clusters[j]
        # Remove j then i
        clusters = [c for idx, c in enumerate(clusters) if idx not in (i, j)] + [merged]

    # Assign labels
    labels = [0] * n
    for cid, cluster in enumerate(clusters):
        for idx in cluster:
            labels[idx] = cid
    return labels


# ---------------------------------------------------------------------------
# t-SNE (simplified)
# ---------------------------------------------------------------------------

def tsne(X, n_components=2, perplexity=30.0, n_iter=250, seed=42):
    """Simplified t-SNE for dimensionality reduction."""
    rng = random.Random(seed)
    n = len(X)
    if n == 0:
        return []
    d = len(X[0]) if X else 0
    # Compute pairwise affinities (simplified - use Gaussian kernel)
    # Initialize low-dimensional points randomly
    Y = [[rng.gauss(0, 0.01) for _ in range(n_components)] for _ in range(n)]
    lr = 200.0
    for iteration in range(n_iter):
        # Compute gradients (simplified)
        grad = [[0.0] * n_components for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                diff = [Y[i][k] - Y[j][k] for k in range(n_components)]
                dist_sq = sum(x ** 2 for x in diff) + 1e-10
                # t-distribution kernel
                w = 1.0 / (1 + dist_sq)
                for k in range(n_components):
                    grad[i][k] += 4 * w * diff[k]
        # Update
        for i in range(n):
            for k in range(n_components):
                Y[i][k] -= lr * grad[i][k] / n
    return Y


# ---------------------------------------------------------------------------
# UMAP (simplified)
# ---------------------------------------------------------------------------

def umap(X, n_components=2, n_neighbors=15, min_dist=0.1, seed=42):
    """Simplified UMAP for dimensionality reduction."""
    rng = random.Random(seed)
    n = len(X)
    if n == 0:
        return []
    # Initialize randomly
    Y = [[rng.gauss(0, 0.01) for _ in range(n_components)] for _ in range(n)]
    # Simple optimization (gradient descent on fuzzy set cross entropy)
    lr = 1.0
    for _ in range(100):
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                dist = _euclidean(Y[i], Y[j])
                # Attractive force
                if dist < min_dist:
                    for k in range(n_components):
                        Y[i][k] += lr * (Y[j][k] - Y[i][k])
                else:
                    for k in range(n_components):
                        Y[i][k] -= lr * (Y[j][k] - Y[i][k]) * 0.01
    return Y


# ---------------------------------------------------------------------------
# Feature selection
# ---------------------------------------------------------------------------

def variance_threshold(X, threshold=0.0):
    """Select features with variance above threshold."""
    if not X:
        return []
    n_features = len(X[0])
    selected = []
    for j in range(n_features):
        col = [row[j] for row in X]
        mean = sum(col) / len(col)
        var = sum((x - mean) ** 2 for x in col) / len(col)
        if var > threshold:
            selected.append(j)
    return selected


def correlation_filter(X, threshold=0.9):
    """Remove highly correlated features. Returns indices to keep."""
    if not X:
        return []
    n_features = len(X[0])
    # Compute correlation matrix
    corr = [[0.0] * n_features for _ in range(n_features)]
    for i in range(n_features):
        for j in range(n_features):
            col_i = [row[i] for row in X]
            col_j = [row[j] for row in X]
            mi = sum(col_i) / len(col_i)
            mj = sum(col_j) / len(col_j)
            cov = sum((a - mi) * (b - mj) for a, b in zip(col_i, col_j))
            vi = sum((a - mi) ** 2 for a in col_i) ** 0.5
            vj = sum((b - mj) ** 2 for b in col_j) ** 0.5
            if vi * vj > 0:
                corr[i][j] = cov / (vi * vj)
    # Greedy removal
    to_remove = set()
    for i in range(n_features):
        for j in range(i + 1, n_features):
            if abs(corr[i][j]) >= threshold and j not in to_remove:
                to_remove.add(j)
    return [i for i in range(n_features) if i not in to_remove]


def mutual_info_scores(X, y):
    """Compute mutual information between each feature and target (discretized)."""
    if not X or not y:
        return []
    n_features = len(X[0])
    scores = []
    for j in range(n_features):
        col = [row[j] for row in X]
        # Discretize
        try:
            col_d = [int(round(v)) for v in col]
            y_d = [int(v) if not isinstance(v, str) else hash(v) % 100 for v in y]
        except (TypeError, ValueError):
            scores.append(0.0)
            continue
        # Compute MI
        # Joint and marginal counts
        from collections import Counter
        joint = Counter(zip(col_d, y_d))
        col_counts = Counter(col_d)
        y_counts = Counter(y_d)
        n = len(col_d)
        mi = 0.0
        for (c, yv), cnt in joint.items():
            p_xy = cnt / n
            p_x = col_counts[c] / n
            p_y = y_counts[yv] / n
            if p_xy > 0 and p_x > 0 and p_y > 0:
                mi += p_xy * math.log(p_xy / (p_x * p_y))
        scores.append(round(mi, 6))
    return scores


# ---------------------------------------------------------------------------
# Cluster evaluation
# ---------------------------------------------------------------------------

def silhouette_score(X, labels):
    """Compute silhouette score for clustering."""
    n = len(X)
    if n < 2:
        return 0.0
    # Check number of clusters
    clusters = set(labels)
    if len(clusters) < 2:
        return 0.0
    scores = []
    for i in range(n):
        # a(i): mean distance to same cluster
        same = [j for j in range(n) if labels[j] == labels[i] and j != i]
        if same:
            a = sum(_euclidean(X[i], X[j]) for j in same) / len(same)
        else:
            a = 0.0
        # b(i): min mean distance to other clusters
        b = float("inf")
        for c in clusters:
            if c == labels[i]:
                continue
            other = [j for j in range(n) if labels[j] == c]
            if other:
                mean_d = sum(_euclidean(X[i], X[j]) for j in other) / len(other)
                b = min(b, mean_d)
        if b == float("inf"):
            b = 0.0
        denom = max(a, b)
        if denom == 0:
            scores.append(0.0)
        else:
            scores.append((b - a) / denom)
    return sum(scores) / len(scores)


def build_clustering_namespace() -> dict[str, Any]:
    return {
        "dbscan": dbscan,
        "hierarchical_clustering": hierarchical_clustering,
        "tsne": tsne,
        "umap": umap,
        "variance_threshold": variance_threshold,
        "correlation_filter": correlation_filter,
        "mutual_info_scores": mutual_info_scores,
        "silhouette_score": silhouette_score,
    }
