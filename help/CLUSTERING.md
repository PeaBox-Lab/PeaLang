# Clustering and dimensionality reduction (v139)

PeaLang provides dependency-free clustering and dimensionality reduction.

## Key functions

- `analysis.dbscan(X, eps, min_samples, metric)` — DBSCAN
- `analysis.hierarchical_clustering(X, n_clusters, linkage)` — hierarchical
- `analysis.tsne(X, n_components, perplexity, n_iter, seed)` — t-SNE
- `analysis.umap(X, n_components, n_neighbors, min_dist, seed)` — UMAP
- `analysis.variance_threshold(X, threshold)` — variance selection
- `analysis.correlation_filter(X, threshold)` — correlation filter
- `analysis.mutual_info_scores(X, y)` — mutual information
- `analysis.silhouette_score(X, labels)` — silhouette score