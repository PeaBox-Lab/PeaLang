# Model Selection

PeaLang's selection layer adds k-fold cross-validation, exhaustive grid search
and seeded random search on top of the [tree](TREE_MODELS.md) and
[boosting](GRADIENT_BOOSTING.md) estimators. It is pure Python with no
third-party dependencies and replaces the scikit-learn
`cross_val_score` / `GridSearchCV` / `RandomizedSearchCV` workflow.

Everything is exposed through:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.
- `analysis.*` — record-friendly wrappers for tables.

## What the layer covers

| Task | Python equivalent | PeaLang |
|---|---|---|
| Cross-validation | `cross_val_score`, `cross_validate` | `stats.cross_validate` |
| Exhaustive search | `GridSearchCV` | `stats.grid_search` |
| Random search | `RandomizedSearchCV` | `stats.random_search` |
| Table wrapper | pandas + scikit-learn | `analysis.tune_model`, `analysis.random_tune` |

## Estimators and parameters

Estimators are named by string, because PeaLang functions are not passed to
native code as callables:

| Name | Aliases | Model |
|---|---|---|
| `"tree"` | `"decision_tree"` | `stats.decision_tree` |
| `"forest"` | `"random_forest"` | `stats.random_forest` |
| `"boosting"` | `"gradient_boosting"`, `"gbm"` | `stats.gradient_boosting` |

Each estimator accepts only its own parameters:

| Estimator | Parameters |
|---|---|
| `tree` | `max_depth`, `min_samples_split`, `min_samples_leaf`, `max_features`, `seed` |
| `forest` | `n_estimators`, `max_depth`, `min_samples_split`, `min_samples_leaf`, `max_features`, `bootstrap`, `seed` |
| `boosting` | `n_estimators`, `learning_rate`, `max_depth`, `min_samples_split`, `min_samples_leaf`, `subsample`, `max_features`, `seed` |

Any other parameter name raises a `ValueError` naming the offender.

## Scoring

`scoring` accepts a metric name or `"auto"`. `"auto"` picks `r2` for
regression and `accuracy` for classification.

| Task | Metrics | Direction |
|---|---|---|
| Regression | `r2`, `explained_variance` | higher is better |
| Regression | `mse`, `rmse`, `mae` | lower is better |
| Classification | `accuracy`, `balanced_accuracy`, `f1`, `roc_auc` | higher is better |
| Classification | `log_loss` | lower is better |

Aliases: `r_squared` / `r2_score` → `r2`, `acc` → `accuracy`, `auc` →
`roc_auc`, `explained` → `explained_variance`.

`roc_auc` and `log_loss` require binary classification with predicted
probabilities; multiclass targets raise a `ValueError`.

## Cross-validation

```pea
let x = [[0], [1], [2], [3], [4], [5], [6], [7]]
let y = [0, 0, 0, 0, 1, 1, 1, 1]

let cv = stats.cross_validate("tree", x, y, "classification", {"max_depth": 2}, 4, 1, "accuracy")
print cv["scoring"]            // accuracy
print cv["folds"]              // 4
print cv["mean"]               // mean score across folds
print cv["std"]                // population standard deviation
print cv["higher_is_better"]   // true
```

`cross_validate(estimator, features, target, task, params, folds, seed, scoring, shuffle)`
returns:

| Field | Meaning |
|---|---|
| `estimator` | Canonical estimator name |
| `task` | `"regression"` or `"classification"` |
| `scoring` | Resolved metric name |
| `params` | Settings used for the fit |
| `scores` | One score per fold |
| `mean`, `std` | Mean and population standard deviation |
| `folds` | Number of folds |
| `higher_is_better` | Sort direction for the metric |
| `seed` | Seed used for shuffling and model randomness |

Classification uses stratified folds when every class has at least `folds`
samples, so each fold keeps the class balance. Otherwise it falls back to plain
k-fold. Regression always uses plain k-fold.

## Grid search

```pea
let grid = {"max_depth": [1, 2, 3], "min_samples_leaf": [1, 2]}
let search = stats.grid_search("tree", x, y, "classification", grid, 4, 1, "accuracy")
print search["best_params"]     // {"max_depth": 1}
print search["best_score"]
print search["n_candidates"]    // 6
print search["best_model"]["estimator"]
```

`grid_search(estimator, features, target, task, param_grid, folds, seed, scoring, shuffle)`
scores every combination of the grid, ranks them and refits the winner on all
rows. The grid maps parameter names to non-empty lists; keys are visited in
sorted order so results are reproducible.

| Field | Meaning |
|---|---|
| `best_params` | Winning parameter combination |
| `best_score`, `best_std` | Cross-validated mean and spread of the winner |
| `best_model` | Winning estimator fitted on every row |
| `results` | Ranked `{params, mean, std, scores}` entries |
| `n_candidates` | Number of combinations evaluated |
| `folds`, `seed`, `scoring`, `higher_is_better` | Run metadata |

`results` is sorted best-first: descending for higher-is-better metrics,
ascending for lower-is-better metrics. Ties keep grid order.

## Random search

```pea
let grid = {"n_estimators": [5, 10, 15], "max_depth": [2, 3]}
let search = stats.random_search("forest", x, y, "classification", grid, 4, 5, 2, "accuracy")
print search["n_candidates"]    // 4
print search["best_params"]
```

`random_search(estimator, features, target, task, param_grid, n_iter, folds, seed, scoring, shuffle)`
samples `n_iter` distinct combinations from the grid and keeps the best. The
sampler is seeded, so the same seed evaluates the same candidates. When the
grid has fewer combinations than `n_iter`, it samples with replacement after
exhausting the distinct options.

Random search is the practical choice for large grids: it usually finds a
near-optimal region with far fewer fits than an exhaustive sweep.

## Record-friendly wrappers

```pea
let rows = [
    {"a": 0, "b": 0, "label": 0},
    {"a": 1, "b": 0, "label": 0},
    {"a": 2, "b": 0, "label": 1},
    {"a": 3, "b": 0, "label": 1},
    {"a": 4, "b": 0, "label": 2},
    {"a": 5, "b": 0, "label": 2}
]

let tuned = analysis.tune_model(rows, "label", ["a", "b"], "tree", "auto", {"max_depth": [1, 2]}, 3, 1, "accuracy")
print tuned["task"]                          // classification
print tuned["features"]                      // ["a", "b"]
print tuned["n_used"]                        // 6
print tuned["best_model"]["importance"][0]["feature"]
```

`analysis.tune_model(data, target, features, estimator, task, param_grid, folds, seed, scoring)`
and
`analysis.random_tune(data, target, features, estimator, task, param_grid, n_iter, folds, seed, scoring)`
build the feature matrix from records, run the search, and add:

| Field | Meaning |
|---|---|
| `features` | Feature column names used |
| `n_used` | Rows with complete features and target |
| `best_model.features` | Feature names stored on the fitted model |
| `best_model.importance` | Sorted `{feature, importance}` table |

`features = null` selects every numeric column except the target. `task =
"auto"` infers classification for boolean, non-numeric and low-cardinality
integer targets and regression otherwise. Rows with missing or non-numeric
feature values, or a missing target, are dropped before tuning.

## Runnable example

- [`examples/use_cases/17_model_selection.pea`](../examples/use_cases/17_model_selection.pea)

```bash
pea run examples/use_cases/17_model_selection.pea
```

The example grid-searches a boosted regressor on a noisy cubic target, re-runs
cross-validation on the winning settings, then random-searches a forest on a
nonlinear two-dimensional classification problem and scores the refitted model.

## Assumptions and limitations

- Only the built-in tree, forest and boosting estimators are searchable. Linear
  models, custom estimators and callable scoring are not supported.
- Estimators are chosen by name, not by passing a function.
- Cross-validation refits from scratch each fold. There is no warm start, so
  large grids on large data are slow.
- `folds` must be at least `2` and at most the number of rows.
- `roc_auc` and `log_loss` need binary probabilities. For multiclass use
  `accuracy`, `balanced_accuracy` or `f1`.
- Selection optimizes one metric at a time. For trade-offs, run separate
  searches and compare the `results` tables.
- The winner is refit on all rows, including the rows used to estimate its
  score, so `best_score` is an optimistic estimate of unseen performance. Hold
  out a final test set when you need an unbiased number.
- Categorical predictors must be encoded numerically first, for example with
  `stats.label_encode` or `stats.ordinal_encode`.
