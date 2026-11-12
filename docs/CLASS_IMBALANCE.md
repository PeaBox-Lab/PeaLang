# Class Imbalance

PeaLang's imbalance layer rebalances classification data before fitting a
[tree](TREE_MODELS.md), [forest](TREE_MODELS.md) or
[boosting](GRADIENT_BOOSTING.md) model. It is pure Python with no third-party
dependencies and covers the common alternatives to scikit-learn's
`imblearn` resamplers.

A classifier trained on rare events usually maximizes accuracy by ignoring the
rare class. Resampling changes the class distribution the model sees, which
trades some majority-class accuracy for much better recall and balanced
accuracy on the minority class.

Everything is exposed through:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.
- `analysis.*` — record-friendly wrapper for tables.

## Measuring imbalance

```pea
let balance = stats.class_balance([0, 0, 0, 0, 1])
print balance["n"]                 // 5
print balance["classes"]           // [0, 1]
print balance["majority"]          // 0
print balance["minority"]          // 1
print balance["imbalance_ratio"]   // 4
print balance["counts"]            // [{class, count, share}, ...]
```

`class_balance(target)` returns:

| Field | Meaning |
|---|---|
| `n` | Number of labels |
| `classes` | Sorted class order |
| `counts` | `{class, count, share}` entries in class order |
| `majority`, `minority` | Largest and smallest classes |
| `imbalance_ratio` | Largest count divided by smallest count |

A ratio near `1` means balanced classes. Ratios above roughly `10` usually
warrant resampling or a cost-sensitive approach.

## Resampling

All resamplers take `features`, `target` and a `seed`, and return the same
shape of record:

```pea
let result = stats.smote(features, labels, 5, 0)
print result["method"]      // "smote"
print result["features"]    // resampled feature rows
print result["target"]      // resampled labels
print result["n"]           // rows after resampling
print result["added"]       // rows created
print result["removed"]     // rows dropped
print result["seed"]
```

| Function | Method | What it does |
|---|---|---|
| `random_oversample` | `"random_oversample"` | Duplicates random minority rows with replacement until every class matches the majority |
| `random_undersample` | `"random_undersample"` | Drops random majority rows without replacement until every class matches the minority |
| `smote` | `"smote"` | Synthesizes minority rows by interpolating between nearest same-class neighbors |

Original rows keep their order and synthetic or kept rows are appended, so
results are reproducible for a given seed.

### Random oversampling

```pea
let over = stats.random_oversample(features, labels, 1)
```

Simple and fast, but it repeats exact rows, which encourages overfitting.
Use it when the minority class is very small or as a baseline.

### Random undersampling

```pea
let under = stats.random_undersample(features, labels, 1)
```

Fast and reduces training time, but throws away majority information. Prefer
it when the majority class is huge and redundant.

### SMOTE

```pea
let synthetic = stats.smote(features, labels, 5, 7)
```

For every class below the majority count, SMOTE picks a base row, finds its
`k` nearest same-class neighbors using Euclidean distance, picks one at random,
and places a new row a random fraction of the way from the base to that
neighbor. The result is a new point inside the minority region rather than a
copy of an existing row.

- `k` is capped at `count - 1` for each class.
- A class with a single row cannot be interpolated, so that row is duplicated.
- Multiclass targets are handled class by class: every class is oversampled to
  the majority count.
- Distances are Euclidean on the numeric columns, so encode categorical
  predictors first with `stats.label_encode` or `stats.ordinal_encode`.

## Record-friendly wrapper

```pea
let balanced = analysis.balance_classes(rows, "label", ["x1", "x2"], "smote", 5, 0)
print balanced["method"]                  // smote
print balanced["n_used"]                  // usable rows before resampling
print balanced["n"]                       // rows after resampling
print balanced["added"]
print balanced["removed"]
print balanced["before"]                  // [{class, count, share}, ...]
print balanced["after"]
print balanced["imbalance_ratio_before"]
print balanced["imbalance_ratio_after"]

let model = analysis.forest_report(balanced["rows"], "label", ["x1", "x2"], "classification")
```

`analysis.balance_classes(data, target, features, method, k, seed)` accepts
`"smote"`, `"oversample"` / `"over"` / `"random_oversample"`, or
`"undersample"` / `"under"` / `"random_undersample"`. `features = null`
selects every numeric column except the target. Rows with missing or
non-numeric feature values, or a missing target, are dropped first.

## Correct workflow

Resample the training data only. Keep the test set at its natural class
distribution so the reported metrics reflect reality.

```pea
let parts = stats.train_test_split(features, labels, 0.3, true, 5, labels)

// fit on resampled training rows
let balanced = stats.smote(parts["X_train"], parts["y_train"], 5, 3)
let model = stats.random_forest(balanced["features"], balanced["target"], "classification", 100, 4)

// score on the untouched test rows
let predicted = stats.predict_forest(model, parts["X_test"])["predicted"]
print stats.balanced_accuracy(parts["y_test"], predicted)
print stats.precision_recall_fscore(parts["y_test"], predicted, 1)["recall"]
```

Resampling the test set would leak synthetic points into evaluation and
inflate the scores.

## Runnable example

- [`examples/use_cases/19_class_imbalance.pea`](../examples/use_cases/19_class_imbalance.pea)

```bash
pea run examples/use_cases/19_class_imbalance.pea
```

The example builds a rare-class problem, shows a baseline forest with low
minority recall, applies SMOTE to the training rows only, and reports the
improvement in accuracy, balanced accuracy and recall. It also prints the
oversampled and undersampled row counts.

## Assumptions and limitations

- Resampling changes the class prior. Predicted probabilities are no longer
  calibrated to the original population; recalibrate with
  [`calibration_curve`](MODEL_EVALUATION.md) or keep the original model when
  probability calibration matters more than recall.
- SMOTE interpolates numeric features. Categorical predictors must be encoded
  numerically first, and interpolated values of encoded categories may not be
  meaningful.
- SMOTE can create points in regions where the minority class does not
  actually occur, especially when classes overlap. Check the resulting model on
  a holdout set.
- Random oversampling duplicates rows and can overfit; random undersampling
  discards information. Compare all three methods with cross-validation from
  [`model selection`](MODEL_SELECTION.md).
- Resampling is not a substitute for more data or better features. If the
  minority signal is weak, resampling will amplify noise.
- All randomness is seeded, but the seed only controls the sampler. Estimators
  have their own seeds, so pass both when you need fully reproducible runs.
- There is no SMOTE variant with borderline or ADASYN weighting, and no
  built-in class-weight support on the estimators.
