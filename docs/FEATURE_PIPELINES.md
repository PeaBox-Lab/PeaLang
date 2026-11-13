# Feature Pipelines

PeaLang's pipeline layer turns raw, mixed and incomplete records into the
numeric matrices that [trees](TREE_MODELS.md) and [boosting](GRADIENT_BOOSTING.md)
expect. It composes imputation, date expansion, target encoding, encoding and
scaling into one fitted transformer and reapplies the learned values to new
rows. It is pure Python with no third-party dependencies and replaces the
scikit-learn `Pipeline` + `ColumnTransformer` + `SimpleImputer` +
`OneHotEncoder` + `StandardScaler` stack.

Everything is exposed through:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.
- `analysis.*` — record-friendly wrappers that fit a model end to end.

## Steps

A pipeline is a list of step records, applied in order:

```pea
let steps = [
    {"op": "impute", "method": "auto"},
    {"op": "date", "parts": ["year", "month", "weekday"]},
    {"op": "target", "columns": ["store"], "smoothing": 10.0},
    {"op": "encode", "method": "onehot"},
    {"op": "scale", "method": "standard"}
]
```

| Step | Methods | Effect |
|---|---|---|
| `impute` | `auto`, `mean`, `median`, `mode`, `constant`, `zero` | Replaces missing values per column |
| `date` | `parts`, `required` | Expands date-like columns into calendar columns |
| `target` | `columns`, `smoothing`, `min_count`, `required` | Replaces categories with smoothed target means |
| `encode` | `onehot`, `ordinal` (alias `label`) | Converts categorical columns to numbers |
| `scale` | `standard`, `minmax` | Centers and scales numeric columns |

Aliases: `fillna` for `impute`, `standardize` for `scale`, `calendar` for
`date`, `target_encode` for `target`.

## Imputation

```pea
let fitted = stats.fit_pipeline([{"op": "impute", "method": "mean"}], features, ["x1", "x2"])
print fitted["features"]
print fitted["steps"][0]["fills"]
print fitted["steps"][0]["missing"]
```

- `mean`, `median` and `zero` require a numeric column.
- `auto` uses the mean for numeric columns and the mode for categorical ones.
- `mode` works for any type; ties resolve in the column's sorted level order.
- `constant` requires a `value` field and fills every column with it.
- A column with no observed values raises an error.

Each fitted fill stores `{name, method, value, missing}` so the same values are
reused on new rows.

## Dates

```pea
let fitted = stats.fit_pipeline(
    [{"op": "date", "parts": ["year", "month", "weekday", "epoch_day"]}],
    features,
    ["when", "region", "spend"],
)
print fitted["names"]
```

Columns whose observed values all parse as dates are replaced by one
`name=part` column per part; other columns pass through. `parts` defaults to
`year`, `month`, `day`, `weekday`, `quarter` and `is_weekend`. Missing dates
must be imputed first. An explicit date step raises when it finds no date
column; add `"required": false` to make it a no-op, which is what
`analysis.model_pipeline` uses. See
[`docs/DATE_FEATURES.md`](DATE_FEATURES.md) for every part and format.

## Target encoding

```pea
let fitted = stats.fit_pipeline(
    [{"op": "target", "columns": ["store"], "smoothing": 10.0}],
    features,
    ["store", "region", "spend"],
    target,
)
print fitted["names"]
print fitted["steps"][0]["columns"]
```

High-cardinality categories become one numeric column instead of a sparse
one-hot block. Each level is replaced by
`(count * mean + smoothing * prior) / (count + smoothing)`; levels seen fewer
than `min_count` times use the overall target mean, as do unseen levels at
transform time. `columns` limits the step to named columns; when omitted, every
non-numeric column is encoded. Numeric columns pass through.

The target is the fourth argument to `stats.fit_pipeline`. A numeric target is
used as-is; a two-class target is mapped to `0`/`1` in sorted class order and
the encoded value is the smoothed share of the second class. More than two
non-numeric classes raise. `required: false` makes the step a no-op when nothing
is categorical.

Target encoding leaks target information on training rows, so fit it on
training data and apply it to held-out rows. PeaLang does not cross-fit it
inside folds. See [`docs/TARGET_ENCODING.md`](TARGET_ENCODING.md) for the full
reference.

## Encoding

```pea
let fitted = stats.fit_pipeline([{"op": "encode", "method": "onehot"}], features, ["region", "plan", "spend"])
print fitted["names"]
print fitted["n_features"]
```

Columns are treated as categorical when at least one observed value is not a
number (booleans count as categorical). Numeric columns pass through unchanged.

- **One-hot** creates one `name=level` column per sorted level. Missing values
  observed during fitting become a `name=null` column. Unseen categories at
  transform time produce an all-zero row for that group.
- **Ordinal** replaces each categorical column with its level index. Missing
  values observed during fitting are a level; unseen categories become `-1`.

Encode categorical columns before scaling. Ordinal codes impose an order, so
prefer one-hot unless the categories are genuinely ordered.

## Scaling

```pea
let fitted = stats.fit_pipeline([{"op": "scale", "method": "standard"}], features, ["x1", "x2"])
print fitted["steps"][0]["columns"]
```

- `standard` subtracts the mean and divides by the sample standard deviation.
  A zero deviation uses a scale of `1`.
- `minmax` subtracts the minimum and divides by the observed range. A zero
  range uses a scale of `1`.

Scaling requires numeric values without missing entries, so impute and encode
first. Trees do not need scaling, but it helps when features live on very
different scales or when a pipeline is reused with distance-based methods.

## Fitting and transforming

```pea
let fitted = stats.fit_pipeline(steps, features, names)
print fitted["steps"]          // fitted step records with learned values
print fitted["features"]       // transformed training rows
print fitted["names"]          // output column names
print fitted["input_names"]    // original column names
print fitted["n_features"]     // output width
print fitted["n"]              // row count

let new = stats.transform_pipeline(fitted, new_features)
print new["features"]
print new["names"]
```

`fit_pipeline(steps, features, names, target)` returns the fitted transformer
with the training rows already transformed. `target` is optional and only
needed by a `target` step. `transform_pipeline(transformer, features)` applies
the stored fill values, levels, date parts, target means, centers and scales to
new rows. The input width must match the fitted `input_names`. `names` defaults
to `x1`, `x2`, ...

Step order matters. A typical order is impute, then date, then target, then
encode, then scale. Scaling before encoding fails on categorical columns,
encoding before imputing can turn missing values into a separate `null`
category, imputing after date expansion cannot fill a calendar column back into
a date, and target encoding needs complete categories and a complete target.

## Model wrapper

```pea
let model = analysis.model_pipeline(
    rows, "churn", ["region", "plan", "tenure", "spend"],
    null, "forest", "auto", {"n_estimators": 100, "max_depth": 4}
)
print model["task"]
print model["n_used"]
print model["features"]           // raw input columns
print model["output_features"]    // transformed columns
print model["train_accuracy"]
print model["importance"]

let scored = analysis.predict_pipeline(model, new_rows)
print scored["predicted"]
print scored["probabilities"]
```

`analysis.model_pipeline(data, target, features, steps, estimator, task, params)`
builds the raw matrix from records, fits the pipeline, fits the estimator and
returns the model record with a stored `preprocessor`. `steps = null` uses
impute, date expansion, one-hot encoding and standardization. A `target` step
receives the training outcomes automatically.

`analysis.predict_pipeline(model, data)` accepts records or a raw matrix,
transforms it with the stored preprocessor and returns the estimator's
prediction record. Rows with a missing target are dropped before fitting;
missing feature values must be handled by an impute step, otherwise the
pipeline raises a clear error.

`task = "auto"` infers classification for boolean, non-numeric and
low-cardinality integer targets. Pass `"regression"` or `"classification"` to
override. `features = null` uses every column except the target, in record
order, including categorical columns.

## Runnable example

- [`examples/use_cases/20_feature_pipeline.pea`](../examples/use_cases/20_feature_pipeline.pea)
- [`examples/use_cases/23_target_encoding.pea`](../examples/use_cases/23_target_encoding.pea)

```bash
pea run examples/use_cases/20_feature_pipeline.pea
pea run examples/use_cases/23_target_encoding.pea
```

The first example builds a churn table with categorical columns plus missing
numeric values, fits a forest through the default pipeline, reports transformed
column names and importance, and scores new records including an unseen region
and a missing tenure. It also calls the `stats` pipeline directly on a feature
matrix. The second compares target encoding with one-hot encoding for a
high-cardinality store column.

## Assumptions and limitations

- Categorical detection is automatic: a column is categorical if any observed
  value is not a number. To force numeric-looking codes through encoding,
  convert them to strings first or encode them before building the matrix.
- One-hot encoding expands width with every level. High-cardinality columns can
  produce very wide matrices; use the `target` step, ordinal encoding or group
  rare levels first.
- Unseen categories do not raise; they become all-zero one-hot rows, `-1`
  ordinal codes or the target-encoding prior. Monitor this on production data.
- Interpolated imputation is not supported: there is no forward fill, linear
  interpolation or model-based imputation in this layer.
- There is no column subsetting step or interaction expansion. Use `analysis`
  helpers or `stats.polynomial_features` before the pipeline when you need
  those.
- Target encoding uses the training target, so its training features are
  optimistic and it does not cross-fit inside folds. Fit it on training data and
  apply it to held-out rows. Numeric and binary targets are supported; encode
  multiclass targets first. See
  [`docs/TARGET_ENCODING.md`](TARGET_ENCODING.md).
- Date detection is a heuristic: only the date component is used and an
  eight-digit string that happens to be a valid date is treated as one. Use
  explicit steps without a date step to opt out. See
  [`docs/DATE_FEATURES.md`](DATE_FEATURES.md).
- The fitted transformer stores levels, fills, date parts, target means and
  scales, not the training rows. It is safe to keep alongside the model, but its
  input column order must be preserved.
- `model_pipeline` drops rows with a missing target but keeps rows with missing
  features, relying on the impute step.
