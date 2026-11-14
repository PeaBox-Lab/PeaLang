# Advanced machine learning (v134)

PeaLang provides dependency-free implementations of common classifiers:

## k-Nearest Neighbors

- `knn_fit(X, y, k=5)` — fit a k-NN classifier
- `knn_predict(model, X)` — predict labels
- `knn_score(model, X, y)` — accuracy score

## Naive Bayes (Gaussian)

- `naive_bayes_fit(X, y)` — fit a Gaussian naive Bayes classifier
- `naive_bayes_predict(model, X)` — predict labels
- `naive_bayes_score(model, X, y)` — accuracy score

## Linear SVM

- `svm_fit(X, y, C, lr, epochs, seed)` — fit a linear SVM via sub-gradient descent
- `svm_predict(model, X)` — predict labels (+1/-1)
- `svm_score(model, X, y)` — accuracy score