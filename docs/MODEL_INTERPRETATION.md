# Model Interpretation

PeaLang's interpretation layer explains fitted [tree](TREE_MODELS.md),
[forest](TREE_MODELS.md) and [boosting](GRADIENT_BOOSTING.md) models with
permutation importance and partial dependence. It is pure Python with no
third-party dependencies and replaces the scikit-learn
`permutation_importance` and `PartialDependenceDisplay` workflow.

Everything is exposed through:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.
- `analysis.*` — record-friendly wrapper for tables.

## Why two kinds of importance

Split-gain importance (`tree_feature_importance`, `forest_feature_importance`,
`boosting_feature_importance`) is cheap but biased toward high-cardinality and
continuous features. Permutation importance measures the actual metric drop when
a column is shuffled, so it answers a different and often more useful question:
how much does the model rely on this feature for its predictions?

| Method | Cost | Bias | Use for |
|---|---|---|---|
| Split gain | Free after fitting | Favors high-cardinality features | Quick ranking |
| Permutation | `n_repeats × n_features` predictions | Model-agnostic | Trustworthy ranking |

## Permutation importance

```pea
let x = [[0], [1], [2], [3], [4], [5]]
let y = [1, 3, 5, 7, 9, 11]
let model = stats.gradient_boosting(x, y, "regression", 40, 0.1, 3)

let report = stats.permutation_importance(model, x, y, "regression", 5, 0, "r2", ["x"])
print report["baseline"]
print report["scoring"]
print report["importances"][0]["feature"]
print report["importances"][0]["mean"]
```

`permutation_importance(model, features, target, task, n_repeats, seed, scoring, names)`
returns:

| Field | Meaning |
|---|---|
| `estimator` | Estimator stored on the model record |
| `task` | `"regression"` or `"classification"` |
| `scoring` | Resolved metric name |
| `baseline` | Score on the untouched data |
| `higher_is_better` | Metric direction |
| `n_repeats`, `seed` | Repetition count and shuffle seed |
| `importances` | Sorted `{feature, mean, std, values}` entries |

The importance of a feature is:

- `baseline - shuffled` for higher-is-better metrics such as `r2` and
  `accuracy`.
- `shuffled - baseline` for lower-is-better metrics such as `rmse` and
  `log_loss`.

Positive values mean the feature helps the model. Values near zero mean the
model ignores it. Negative values can appear when a feature adds noise and
shuffling happens to help by chance, especially with few repeats.

Each column is shuffled independently. The row order is drawn from `seed`, so
the same seed produces the same importances. Classification metrics that need
probabilities, such as `roc_auc` and `log_loss`, work as long as the estimator
returns them; `tree` predictions do not, so use `forest` or `boosting` for those
metrics.

## Partial dependence

```pea
let curve = stats.partial_dependence(model, x, ["x"], 5, "regression", ["x"])["curves"][0]
print curve["feature"]
print curve["values"]       // evenly spaced grid over the observed range
print curve["average"]      // mean prediction at each grid point
```

`partial_dependence(model, features, columns, grid_size, task, names)` builds a
grid of `grid_size` evenly spaced values between the observed minimum and
maximum of each selected column. At every grid point the column is set for all
rows, the model is scored, and predictions are averaged. This shows the shape of
the learned relationship: flat, rising, thresholded, or U-shaped.

| Field | Meaning |
|---|---|
| `estimator`, `task`, `grid_size` | Run metadata |
| `curves` | One entry per selected column |

`columns` accepts indices, names (when `names` is supplied), or `null` for every
feature. Curves carry:

| Field | Regression | Classification |
|---|---|---|
| `feature` | Feature name | Feature name |
| `values` | Grid values | Grid values |
| `average` | Mean prediction | Mean probability of the last class |
| `classes` | — | Class order |
| `probabilities` | — | One averaged probability list per class |

For binary problems the last class is the positive class, so `average` is the
positive-class probability curve. For multiclass problems `probabilities` holds
one curve per class and `average` is the last class's curve. Each grid point's
class probabilities sum to `1`.

## Record-friendly wrapper

```pea
let rows = [
    {"x": 0, "noise": 0.1, "y": 1},
    {"x": 1, "noise": 0.4, "y": 3},
    {"x": 2, "noise": 0.2, "y": 5},
    {"x": 3, "noise": 0.9, "y": 7},
    {"x": 4, "noise": 0.5, "y": 9}
]

let model = analysis.interpret_report(rows, "y", ["x", "noise"], "boosting", "regression", {"n_estimators": 40, "learning_rate": 0.1}, 5, 10, 0, "r2", ["x"])
print model["permutation_importance"][0]["feature"]
print model["partial_dependence"][0]["average"]
```

`analysis.interpret_report(data, target, features, estimator, task, params, n_repeats, grid_size, seed, scoring, columns)`
fits the estimator from records, then adds:

| Field | Meaning |
|---|---|
| `features` | Feature column names used |
| `importance` | Split-gain importance table |
| `permutation_importance` | Sorted permutation importance table |
| `partial_dependence` | Partial dependence curves |
| `baseline` | Untouched-data score |
| `scoring` | Resolved metric name |
| `n_used` | Rows with complete features and target |

`estimator` accepts `"tree"`, `"forest"` or `"boosting"`; `params` is the same
dict used by [model selection](MODEL_SELECTION.md). `features = null` selects
every numeric column except the target. `task = "auto"` infers classification
for boolean, non-numeric and low-cardinality integer targets. Rows with missing
or non-numeric feature values, or a missing target, are dropped before fitting.

## Runnable example

- [`examples/use_cases/18_model_interpretation.pea`](../examples/use_cases/18_model_interpretation.pea)

```bash
pea run examples/use_cases/18_model_interpretation.pea
```

The example explains a boosted regressor on a noisy cubic target, ranks signal
above noise for a nonlinear classifier, reads a probability curve from partial
dependence, and calls the `stats` helpers directly on an already-fitted model.

## Assumptions and limitations

- Permutation importance is measured on the data you pass in. On training rows
  it can understate importance for features the model overfits; prefer a
  holdout set for a realistic ranking.
- Shuffling breaks feature correlations, so importance is misleading when
  predictors are strongly correlated. Use grouped or conditional variants for
  those cases.
- `n_repeats` controls noise. A handful of repeats is enough for a rough
  ranking; use more when means are close.
- Partial dependence averages over the observed joint distribution, so it can
  show combinations that never occur in the data. Treat it as a summary, not a
  causal effect.
- Classification partial dependence averages probabilities, not decisions.
- `tree` models do not expose probabilities, so probability-based metrics and
  probability curves need `forest` or `boosting`.
- Categorical predictors must be encoded numerically first, for example with
  `stats.label_encode` or `stats.ordinal_encode`.
- These tools explain the model, not the world. A feature can be important to
  the model without causing the outcome.
