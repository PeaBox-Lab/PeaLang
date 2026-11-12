# Model Evaluation, Resampling and Feature Preparation

PeaLang's evaluation layer sits above [`modeling`](ADVANCED_MODELING.md) and
answers the practical question a model has to pass: how well does it
generalize? It provides train/test splitting, k-fold and stratified k-fold
index generators, classification and regression metrics, ROC/AUC, probability
scoring, calibration, and feature encoders and transforms.

Everything is pure Python, has no third-party dependencies, and is exposed
through:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.
- `analysis.*` — record-friendly wrappers for tables.

## What the layer covers

| Task | Python equivalent | PeaLang |
|---|---|---|
| Train/test split | `sklearn.model_selection.train_test_split` | `stats.train_test_split` |
| k-fold indices | `KFold` | `stats.k_fold` |
| Stratified folds | `StratifiedKFold` | `stats.stratified_k_fold` |
| Classification metrics | `sklearn.metrics` | `stats.accuracy_score`, `stats.precision_recall_fscore`, `stats.balanced_accuracy` |
| Ranking metrics | `roc_auc_score`, `roc_curve` | `stats.roc_auc`, `stats.roc_curve` |
| Probability metrics | `log_loss`, `brier_score_loss` | `stats.log_loss`, `stats.brier_score`, `stats.calibration_curve` |
| Regression metrics | `mean_squared_error`, `r2_score` | `stats.mean_squared_error`, `stats.r2_score`, ... |
| Feature expansion | `PolynomialFeatures` | `stats.polynomial_features` |
| Encoding | `LabelEncoder`, `OrdinalEncoder` | `stats.label_encode`, `stats.ordinal_encode` |
| Scaling | `StandardScaler`, `MinMaxScaler` | `stats.standardize_features`, `stats.minmax_features` |
| Record wrappers | pandas + scikit-learn | `analysis.train_test_split`, `analysis.evaluate_classification`, `analysis.evaluate_regression`, `analysis.add_polynomial_features` |

## Train/test splitting

`stats.train_test_split(features, target, test_size, shuffle, seed, stratify)`
returns the split arrays, the original row indices, and the split sizes.

```pea
let x = [[1], [2], [3], [4], [5], [6], [7], [8], [9], [10]]
let y = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]

let split = stats.train_test_split(x, y, 0.3, true, 7)
print split["n_train"]
print split["n_test"]
print split["test_index"]

// keep the class proportions in both halves
let stratified = stats.train_test_split(x, y, 0.3, true, 7, y)
print stratified["stratified"]
```

- `test_size` is the fraction of rows placed in the test set.
- With `shuffle = false`, the first `n_test` rows become the test set, which is
  useful for ordered or time-ordered data.
- `stratify` accepts one label per row. Test slots are allocated across strata
  by largest remainder, so the requested size is met exactly.
- The split is deterministic for a given `seed`.

## Cross-validation

`stats.k_fold(samples, k, shuffle, seed)` and
`stats.stratified_k_fold(labels, k, shuffle, seed)` return a list of folds.
Each fold has disjoint `train` and `test` index lists.

```pea
let folds = stats.k_fold(len(rows), 5, true, 3)
for fold in folds {
    print fold["fold"] + ": " + str(fold["n_train"]) + "/" + str(fold["n_test"])
}
```

`stratified_k_fold` requires each class to have at least `k` samples; it raises
a clear error instead of silently producing folds that miss a class.

Because PeaLang functions are not first-class callables passed to native code,
cross-validation is written as a loop: build the fold arrays, fit, predict, and
score. The runnable example shows the full pattern.

## Classification metrics

```pea
let actual    = [0, 0, 1, 1, 1, 0]
let predicted = [0, 1, 1, 1, 0, 0]

print stats.accuracy_score(actual, predicted)
print stats.balanced_accuracy(actual, predicted)
let report = stats.precision_recall_fscore(actual, predicted)
print report["precision"]
print report["recall"]
print report["f1"]
print report["per_class"]
```

`precision_recall_fscore` returns per-class precision, recall, F1 and support,
plus macro, weighted and micro summaries. Top-level `precision`, `recall` and
`f1` refer to the positive class for binary data and to the macro average for
multiclass data. Pass `positive` to choose the positive label explicitly.

`balanced_accuracy` is the mean per-class recall and is the right summary when
classes are imbalanced.

## Ranking and probability metrics

```pea
let scores = [0.1, 0.4, 0.35, 0.8]

print stats.roc_auc([0, 0, 1, 1], scores)
let curve = stats.roc_curve([0, 0, 1, 1], scores)
print curve["fpr"]
print curve["tpr"]
print curve["thresholds"]

print stats.log_loss([0, 0, 1, 1], scores)
print stats.brier_score([0, 0, 1, 1], scores)

let calibration = stats.calibration_curve([0, 0, 1, 1], scores, 5)
print calibration["table"]
```

- `roc_auc` is tie-aware: it uses mid-ranks, so identical scores contribute
  `0.5` correctly.
- `log_loss` clips probabilities with `epsilon` (default `1e-15`) before taking
  logs.
- `brier_score` is the mean squared error between probabilities and outcomes.
- `calibration_curve` bins probabilities and reports the mean predicted
  probability and observed positive rate per bin. Empty bins are returned with
  `null` values so the bin layout stays fixed.

## Regression metrics

```pea
let actual    = [3, -0.5, 2, 7]
let predicted = [2.5, 0.0, 2, 8]

print stats.mean_squared_error(actual, predicted)
print stats.root_mean_squared_error(actual, predicted)
print stats.mean_absolute_error(actual, predicted)
print stats.median_absolute_error(actual, predicted)
print stats.mean_absolute_percentage_error(actual, predicted)
print stats.r2_score(actual, predicted)
print stats.explained_variance_score(actual, predicted)
```

`r2_score` returns `1` for a perfect fit and handles a constant target by
returning `1` only when the residuals are also zero. `mean_absolute_percentage_error`
returns a fraction (`0.1` means 10%) and rejects zero actual values.

## Feature preparation

### Polynomial expansion

```pea
let expanded = stats.polynomial_features([[2, 3], [4, 5]], 2)
print expanded["names"]
print expanded["features"]

// interactions only, no pure powers
print stats.polynomial_features([[2, 3]], 2, false, true)["names"]

// include a bias column
print stats.polynomial_features([[2, 3]], 1, true)["names"]
```

Names follow `x1`, `x2`, `x1^2`, `x1*x2`, `x2^2`. Pass `names` to label the
input columns, or `include_bias` to prepend a constant `1` column.

### Encoding

```pea
let encoded = stats.label_encode(["red", "green", "red", "blue"])
print encoded["codes"]
print encoded["classes"]

let ordered = stats.ordinal_encode(["low", "high", "medium"], ["low", "medium", "high"])
print ordered["codes"]
```

`label_encode` assigns codes in first-seen order. `ordinal_encode` uses an
explicit order, or a sorted order when none is supplied, and rejects values
outside that order.

### Scaling

```pea
let scaled = stats.standardize_features([[1, 10], [2, 20], [3, 30]])
print scaled["means"]
print scaled["stds"]
print scaled["features"]

// apply the training statistics to new rows
print stats.standardize_transform([[4, 40]], scaled["means"], scaled["scales"])

let bounded = stats.minmax_features([[1, 10], [2, 20], [3, 30]])
print bounded["features"]
print stats.minmax_transform([[4, 40]], bounded["mins"], bounded["ranges"])
```

Fit the transform on training data only, then apply the learned `means` and
`scales` (or `mins` and `ranges`) to validation and test rows.

## Record-friendly wrappers

```pea
let rows = [
    {"y": 1, "p": 1.1},
    {"y": 2, "p": 1.9},
    {"y": 3, "p": 3.2}
]

let split = analysis.train_test_split(rows, 0.34, 1)
print split["n_train"]
print split["n_test"]

let metrics = analysis.evaluate_regression(rows, "y", "p")
print metrics["r2"]
print metrics["rmse"]

let quality = analysis.evaluate_classification(rows, "actual", "predicted", "score")
print quality["accuracy"]
print quality["roc_auc"]

let expanded = analysis.add_polynomial_features(rows, ["x1", "x2"], 2)
```

- `train_test_split(data, test_size, seed, stratify, shuffle)` returns `train`
  and `test` record lists.
- `evaluate_regression(data, actual, predicted)` returns `mse`, `rmse`, `mae`,
  `median_ae`, `r2` and `explained_variance`.
- `evaluate_classification(data, actual, predicted, scores, positive)` returns
  the classification report and, when `scores` is given, `roc_auc`, `log_loss`
  and `brier_score`.
- `add_polynomial_features(data, columns, degree, interaction_only, prefix)`
  appends generated columns and leaves input columns untouched.

Wrappers drop rows with missing values in the required columns.

## Runnable example

- [`examples/use_cases/14_model_evaluation.pea`](../examples/use_cases/14_model_evaluation.pea)

```bash
pea run examples/use_cases/14_model_evaluation.pea
```

The example splits a regression sample, scores a holdout set, runs a manual
five-fold cross-validation loop, evaluates a logistic classifier with ROC/AUC
and log loss, and demonstrates polynomial expansion, encoding and scaling.

## Assumptions and limitations

- `train_test_split` shuffles rows. For time series, pass `shuffle = false` or
  split by time explicitly; random splits leak future information.
- Cross-validation is a manual loop over the fold indices. There is no
  single-call estimator protocol because PeaLang functions are not passed to
  native code as callables.
- Metrics expect clean, aligned lists. The `analysis` wrappers drop incomplete
  rows; the `stats` functions raise on mismatched lengths.
- `stratified_k_fold` raises when a class has fewer than `k` samples.
- `polynomial_features` grows combinatorially with the number of columns and
  the degree; cap the degree for wide feature sets.
- Feature scalers do not handle `null`; clean or impute before scaling.
- `roc_curve` returns rates at the distinct observed scores, without the
  artificial `(0, 0)` and `(1, 1)` endpoints. `auc` is computed with the
  tie-aware rank statistic and matches `roc_auc`.
