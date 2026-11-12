# Gradient Boosted Trees

PeaLang's boosting layer adds gradient boosted decision trees for regression,
binary classification and multiclass classification. It builds on the
[tree engine](TREE_MODELS.md) and is pure Python with no third-party
dependencies.

Boosting fits many small, shallow trees in sequence, each one correcting the
errors of the ensemble so far. It is usually the strongest off-the-shelf model
for tabular data and a natural next step after
[random forests](TREE_MODELS.md).

Everything is exposed through:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.
- `analysis.*` — record-friendly wrappers for tables.

## What the layer covers

| Task | Python equivalent | PeaLang |
|---|---|---|
| Regression boosting | `GradientBoostingRegressor` | `stats.gradient_boosting(..., "regression")` |
| Binary classification | `GradientBoostingClassifier` | `stats.gradient_boosting(..., "classification")` with two classes |
| Multiclass classification | `GradientBoostingClassifier` | `stats.gradient_boosting(..., "classification")` with more than two classes |
| Predict | `.predict`, `.predict_proba` | `stats.predict_boosting` |
| Importance | `.feature_importances_` | `stats.boosting_feature_importance` |
| Record wrapper | pandas + scikit-learn | `analysis.boosting_report` |

## Regression

```pea
let x = [[0], [1], [2], [3], [4], [5]]
let y = [1, 3, 5, 7, 9, 11]

let model = stats.gradient_boosting(x, y, "regression", 40, 0.1, 3)
print model["base"]
print model["n_estimators"]

let predicted = stats.predict_boosting(model, x)["predicted"]
print predicted
```

`gradient_boosting(features, target, task, n_estimators, learning_rate, max_depth, min_samples_split, min_samples_leaf, subsample, max_features, seed)`
returns a model record:

| Field | Meaning |
|---|---|
| `estimator` | `"gradient_boosting"` |
| `task` | `"regression"` or `"classification"` |
| `stages` | One list of trees per boosting round; one tree for regression/binary, one per class for multiclass |
| `n_estimators` | Number of boosting rounds |
| `learning_rate` | Shrinkage applied to each stage |
| `base` | Initial prediction (mean, log-odds, or per-class log priors) |
| `classes` | Sorted class labels for classification |
| `feature_importances` | Normalized average split-gain importance |
| `n_features`, `n` | Input width and training rows |
| `max_depth`, `min_samples_split`, `min_samples_leaf` | Base-tree stopping rules |
| `subsample`, `max_features`, `seed` | Sampling settings |

## Binary classification

```pea
let x = [[0], [1], [2], [3], [4], [5]]
let labels = [0, 0, 0, 1, 1, 1]

let model = stats.gradient_boosting(x, labels, "classification", 40, 0.1, 3)
print model["classes"]

let result = stats.predict_boosting(model, [[0], [5]])
print result["predicted"]        // [0, 1]
print result["probabilities"]    // [[1.0, 0.0], [0.0, 1.0]]
```

For two classes the model stores log-odds. Each stage fits a regression tree to
the residual `y - p`, replaces leaf values with the Newton step
`sum(residual) / sum(p * (1 - p))`, and adds the shrunk leaf value to the raw
score. Probabilities are the logistic transform of the final score.

## Multiclass classification

```pea
let labels = [0, 0, 1, 1, 2, 2]
let model = stats.gradient_boosting(x, labels, "classification", 40, 0.1, 3)
print model["classes"]

let result = stats.predict_boosting(model, [[0], [5]])
print result["predicted"]
print result["probabilities"]
```

With more than two classes the model keeps one raw score per class. Each round
fits one regression tree per class to the softmax residual
`(y == k) - p_k`, applies the Friedman multiplier `(K - 1) / K` to the Newton
leaf update, and adds the shrunk value to that class's score. Predictions take
the highest softmax probability.

## How the ensemble is built

- **Initialization.** Regression starts at the target mean. Binary
  classification starts at the log-odds of the positive rate. Multiclass starts
  at per-class log priors.
- **Stage fitting.** Each round fits shallow regression trees to the current
  negative gradient. The trees reuse the CART split search from
  [`trees`](TREE_MODELS.md), so `max_depth`, `min_samples_split`,
  `min_samples_leaf` and `max_features` behave the same way.
- **Leaf values.** Binary and multiclass leaves are replaced by the Newton
  step for their loss, which converges faster and is better calibrated than
  using the mean residual directly.
- **Shrinkage.** Every stage update is multiplied by `learning_rate`.
  Smaller rates need more trees but generalize better; `0.05`–`0.2` is a
  reasonable range.
- **Row subsampling.** `subsample` below `1` fits each stage on a random subset
  of rows (stochastic gradient boosting). This adds regularization and speed.
  The sample is seeded, so results are reproducible.
- **Feature subsampling.** `max_features` limits the predictors considered at
  each split. Accepts an integer, a fraction, `"sqrt"`, `"log2"`, `"all"` or
  `null` (all features).
- **Depth cap.** `max_depth = null` is capped internally at `100` for
  recursion safety. Boosting normally uses shallow trees such as depth `2`–`4`.

## Prediction

`predict_boosting(model, features)` returns:

```pea
// regression
{"predicted": [1.0, 3.0, 5.0, 7.0, 9.0, 11.0]}

// classification
{
    "predicted": [0, 1],
    "probabilities": [[1.0, 0.0], [0.0, 1.0]],
    "classes": [0, 1]
}
```

## Feature importance

```pea
let table = stats.boosting_feature_importance(model, ["signal", "noise"])
print table[0]["feature"]
print table[0]["importance"]
```

Importance averages the normalized split-gain importance of every fitted tree
and renormalizes to sum to `1` when any split exists. The table is sorted by
descending importance and then by name. Omit `names` to get `x1`, `x2`, ...

## Record-friendly wrapper

```pea
let rows = [
    {"x": 0, "y": 0},
    {"x": 1, "y": 0},
    {"x": 2, "y": 0},
    {"x": 3, "y": 1},
    {"x": 4, "y": 1},
    {"x": 5, "y": 1}
]

let report = analysis.boosting_report(rows, "y", ["x"], "auto", 40, 0.1, 3)
print report["task"]
print report["train_accuracy"]
print report["importance"][0]["feature"]
```

`analysis.boosting_report(data, target, features, task, n_estimators, learning_rate, max_depth, min_samples_split, min_samples_leaf, subsample, max_features, seed)`
builds the feature matrix from records, fits the ensemble, and adds:

| Field | Meaning |
|---|---|
| `features` | Feature column names used |
| `importance` | Sorted `{feature, importance}` table |
| `train_predictions` | In-sample predictions |
| `train_r2`, `train_rmse` | Regression diagnostics |
| `train_accuracy` | Classification diagnostic |
| `train_log_loss` | Binary classification log loss |
| `n_used` | Rows with complete features and target |

`features = null` selects every numeric column except the target. `task =
"auto"` treats boolean, non-numeric, and low-cardinality integer targets as
classification and everything else as regression. Pass `"regression"` or
`"classification"` to override.

Rows with missing or non-numeric feature values, or a missing target, are
dropped before fitting.

## Runnable example

- [`examples/use_cases/16_gradient_boosting.pea`](../examples/use_cases/16_gradient_boosting.pea)

```bash
pea run examples/use_cases/16_gradient_boosting.pea
```

The example trains on a holdout split and scores the test set for all three
tasks: cubic regression with R² and RMSE, nonlinear binary classification with
accuracy, ROC/AUC and log loss, and overlapping multiclass classification with
accuracy and class probabilities.

## Assumptions and limitations

- Boosting splits on numeric thresholds only. Encode categorical predictors
  numerically first, for example with `stats.label_encode` or
  `stats.ordinal_encode`.
- There is no early stopping and no validation-based stage selection. Choose
  `n_estimators`, `learning_rate` and `max_depth` with a holdout or
  cross-validation loop from [`evaluation`](MODEL_EVALUATION.md).
- There is no L1/L2 leaf regularization or minimum gain threshold beyond the
  base-tree stopping rules.
- Boosting can overfit noisy data as `n_estimators` grows. Prefer a smaller
  learning rate with more trees, and monitor a validation score.
- Split-gain importance is biased toward high-cardinality and continuous
  features. Use it for ranking, not for causal claims.
- Multiclass training cost grows linearly with the number of classes, since
  each round fits one tree per class.
- `predict_boosting` expects the same feature order and width used during
  fitting; it does not validate against a stored schema.
- The model record stores full trees and can be large. For deployment, keep the
  ensemble small or export predictions instead of the model.
