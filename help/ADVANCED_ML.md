# Advanced machine learning (v134)

PeaLang provides dependency-free implementations of common classifiers.

## k-Nearest Neighbors
- `analysis.knn_fit(X, y, k)` — fit
- `analysis.knn_predict(model, X)` — predict
- `analysis.knn_score(model, X, y)` — score

## Naive Bayes (Gaussian)
- `analysis.naive_bayes_fit(X, y)` — fit
- `analysis.naive_bayes_predict(model, X)` — predict
- `analysis.naive_bayes_score(model, X, y)` — score

## Linear SVM
- `analysis.svm_fit(X, y, C, lr, epochs, seed)` — fit
- `analysis.svm_predict(model, X)` — predict
- `analysis.svm_score(model, X, y)` — score