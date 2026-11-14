# Clustering and dimensionality reduction (v139)

PeaLang provides dependency-free clustering and dimensionality reduction.

## Clustering

- `dbscan(X, eps, min_samples, metric)` — DBSCAN clustering
- `hierarchical_clustering(X, n_clusters, linkage)` — agglomerative clustering
- `silhouette_score(X, labels)` — cluster evaluation

## Dimensionality reduction

- `tsne(X, n_components, perplexity, n_iter, seed)` — t-SNE
- `umap(X, n_components, n_neighbors, min_dist, seed)` — UMAP

## Feature selection

- `variance_threshold(X, threshold)` — variance-based feature selection
- `correlation_filter(X, threshold)` — correlation-based feature removal
- `mutual_info_scores(X, y)` — mutual information scores