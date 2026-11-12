# Decision Trees and Random Forests

PeaLang's tree layer adds CART decision trees and bagged random forests for
tabular regression and classification. It sits above
[`modeling`](ADVANCED_MODELING.md) and [`evaluation`](MODEL_EVALUATION.md),
and is pure Python with no third-party dependencies.

Trees are the right tool when the relationship is nonlinear, when features
interact, or when the audience needs an interpretable split structure. Forests
trade interpretability for stability and accuracy.

Everything is exposed through:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.
- `analysis.*` — record-friendly wrappers for tables.

## What the layer covers

| Task | Python equivalent | PeaLang |
|---|---|---|
| Regression tree | `DecisionTreeRegressor` | `stats.decision_tree(..., "regression")` |
| Classification tree | `DecisionTreeClassifier` | `stats.decision_tree(..., "classification")` |
| Predict with a tree | `.predict`, `.predict_proba` | `stats.predict_tree` |
| Tree importance | `.feature_importances_` | `stats.tree_feature_importance` |
| Random forest | `RandomForestRegressor`, `RandomForestClassifier` | `stats.random_forest` |
| Predict with a forest | `.predict`, `.predict_proba` | `stats.predict_forest` |
| Forest importance | `.feature_importances_` | `stats.forest_feature_importance` |
| Record wrappers | pandas + scikit-learn | `analysis.tree_report`, `analysis.forest_report` |

## Decision trees

```pea
let x = [[0], [1], [2], [3], [4], [5]]
let y = [0, 0, 0, 1, 1, 1]

let tree = stats.decision_tree(x, y, "classification", 3)
print tree["task"]          // classification
print tree["classes"]       // [0, 1]
print tree["n"]             // 6

let result = stats.predict_tree(tree, [[0], [5]])
print result["predicted"]      // [0, 1]
print result["probabilities"]  // [[1.0, 0.0], [0.0, 1.0]]
```

`decision_tree(features, target, task, max_depth, min_samples_split, min_samples_leaf, max_features, seed)`
returns a model record:

| Field | Meaning |
|---|---|
| `estimator` | `"decision_tree"` |
| `task` | `"regression"` or `"classification"` |
| `tree` | Nested split nodes; leaves carry `value` and `n` |
| `classes` | Sorted class labels for classification |
| `feature_importances` | Normalized split-gain importance per feature |
| `n_features` | Number of input columns |
| `n` | Number of training rows |
| `max_depth` | Effective depth limit |
| `min_samples_split`, `min_samples_leaf` | Stopping rules |
| `max_features`, `seed` | Split sampling settings |

Split nodes contain `feature`, `threshold`, `gain`, `n`, `left` and `right`.
Leaf nodes contain `leaf: true`, `value`, `n` and, for classification,
`probabilities`.

### How splits are chosen

- **Regression** trees minimize squared error. Each candidate threshold is
  scored with the closed-form sum of squares, so fitting stays fast without
  materializing the left and right arrays per split.
- **Classification** trees minimize Gini impurity.
- `max_depth` defaults to no explicit limit, capped internally at `100` for
  recursion safety.
- `min_samples_split` (default `2`) is the smallest node that may split.
- `min_samples_leaf` (default `1`) is the smallest allowed child.
- `max_features` limits the predictors considered at each split. Accepts an
  integer, a fraction between 0 and 1, `"sqrt"`, `"log2"`, `"all"` or `null`.
  Sampling is seeded, so results are reproducible.
- A node becomes a leaf when it is pure, reaches the depth limit, is too small,
  or no split improves the cost.

## Prediction

`predict_tree(model, features)` returns:

```pea
// regression
{"predicted": [4.0, 9.0]}

// classification
{
    "predicted": [0, 1],
    "probabilities": [[1.0, 0.0], [0.0, 1.0]],
    "classes": [0, 1]
}
```

Classification probabilities come from the class frequencies in the leaf.
Tie-breaking for the predicted label follows the class order, so results are
stable.

## Feature importance

```pea
let table = stats.tree_feature_importance(tree, ["signal", "noise"])
print table[0]["feature"]
print table[0]["importance"]
```

Importance is the accumulated split gain per feature, normalized to sum to
`1` when any split exists. The table is sorted by descending importance and
then by name. Omit `names` to get `x1`, `x2`, ...

## Random forests

```pea
let forest = stats.random_forest(x, y, "classification", 100, 6, 2, 1, "sqrt", true, 7)
print forest["n_estimators"]
print forest["oob_score"]

let result = stats.predict_forest(forest, [[0], [5]])
print result["predicted"]
print result["probabilities"]
```

`random_forest(features, target, task, n_estimators, max_depth, min_samples_split, min_samples_leaf, max_features, bootstrap, seed)`
returns a model record with `trees`, `n_estimators`, `classes`,
`feature_importances`, `oob_score`, `oob_predictions`, `bootstrap` and the
usual metadata.

- Each tree is grown on a bootstrap sample and considers `max_features`
  predictors at each split. `max_features` defaults to `"sqrt"` for forests.
- Regression predictions average the tree outputs.
- Classification predictions average the leaf class probabilities across trees
  and take the highest-probability class.
- `forest_feature_importance` averages the per-tree normalized importances and
  returns the same sorted table as the tree version.

### Out-of-bag scoring

With `bootstrap = true`, every tree leaves out roughly a third of the rows.
Each row is scored using only the trees that did not see it, giving a
validation estimate without a separate split.

- `oob_score` is `1 - residual/total` variance for regression, and accuracy
  for classification.
- `oob_predictions` holds the averaged regression prediction, the majority
  class, or `null` when a row was never out of bag.
- With `bootstrap = false`, `oob_score` is `null` and `oob_predictions` is
  empty.

OOB estimates are noisy for small samples. Treat them as a quick sanity check,
not a replacement for a proper holdout or cross-validation.

## Record-friendly wrappers

```pea
let rows = [
    {"x": 0, "y": 0},
    {"x": 1, "y": 0},
    {"x": 2, "y": 0},
    {"x": 3, "y": 1},
    {"x": 4, "y": 1},
    {"x": 5, "y": 1}
]

let report = analysis.tree_report(rows, "y", ["x"], "auto", 3)
print report["task"]              // classification
print report["n_used"]
print report["train_accuracy"]
print report["importance"][0]["feature"]

let forest = analysis.forest_report(rows, "y", null, "auto", 25, 4, 2, 1, "sqrt", true, 7)
print forest["oob_score"]
print forest["features"]
```

`analysis.tree_report(data, target, features, task, max_depth, min_samples_split, min_samples_leaf)`
and
`analysis.forest_report(data, target, features, task, n_estimators, max_depth, min_samples_split, min_samples_leaf, max_features, bootstrap, seed)`
build the feature matrix from records, fit the model, and add:

| Field | Meaning |
|---|---|
| `features` | Feature column names used |
| `importance` | Sorted `{feature, importance}` table |
| `train_predictions` | In-sample predictions |
| `train_r2`, `train_rmse` | Regression diagnostics |
| `train_accuracy` | Classification diagnostic |
| `n_used` | Rows with complete features and target |

`features = null` selects every numeric column except the target. `task =
"auto"` treats boolean targets and numeric `0`/`1` targets as classification
and everything else as regression. Pass `"regression"` or `"classification"`
to override.

Rows with missing or non-numeric feature values, or a missing target, are
dropped before fitting.

## Runnable example

- [`examples/use_cases/15_trees_forests.pea`](../examples/use_cases/15_trees_forests.pea)

```bash
pea run examples/use_cases/15_trees_forests.pea
```

The example fits a regression tree and forest to a nonlinear target, reports
R², RMSE and OOB R², then fits classification models on a two-feature
nonlinear region and inspects accuracy, OOB accuracy and feature importance.

## Assumptions and limitations

- Trees split on numeric thresholds only. Encode categorical predictors
  numerically first, for example with `stats.label_encode` or
  `stats.ordinal_encode`.
- Trees are greedy and unstable: small data changes can produce different
  splits. Use a forest, or average several seeds, when stability matters.
- There is no pruning, cost-complexity pruning, or surrogate split handling.
- `max_depth = null` grows until the data is pure or the internal cap of
  `100` is reached, which can overfit small noisy samples.
- Importance from split gain is biased toward high-cardinality and continuous
  features. Use it for ranking, not for causal claims.
- OOB scoring assumes bootstrap sampling and enough trees; with few trees some
  rows may never be out of bag.
- `predict_*` expects the same feature order and width used during fitting; it
  does not validate against a stored schema.
- Feature scalers are unnecessary for trees, since splits are invariant to
  monotone transformations.
- Fitting cost grows with rows × features × candidate thresholds. For very
  large tables, cap `max_depth`, raise `min_samples_leaf`, or reduce
  `max_features`.
