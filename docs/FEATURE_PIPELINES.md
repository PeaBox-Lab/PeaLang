# Feature Pipelines

PeaLang's pipeline layer turns raw, mixed and incomplete records into the
numeric matrices that [trees](TREE_MODELS.md) and [boosting](GRADIENT_BOOSTING.md)
expect. It composes imputation, date expansion, encoding and scaling into one
fitted transformer and reapplies the learned values to new rows. It is pure
Python with no third-party dependencies and replaces the scikit-learn `Pipeline`
+ `ColumnTransformer` + `SimpleImputer` + `OneHotEncoder` + `StandardScaler`
stack.

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
    {"op": "encode", "method": "onehot"},
    {"op": "scale", "method": "standard"}
]
```

| Step | Methods | Effect |
|---|---|---|
| `impute` | `auto`, `mean`, `median`, `mode`, `constant`, `zero` | Replaces missing values per column |
| `date` | `parts`, `required` | Expands date-like columns into calendar columns |
| `encode` | `onehot`, `ordinal` (alias `label`) | Converts categorical columns to numbers |
| `scale` | `standard`, `minmax` | Centers and scales numeric columns |

Aliases: `fillna` for `impute`, `standardize` for `scale`, `calendar` for
`date`.

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

`fit_pipeline(steps, features, names)` returns the fitted transformer with the
training rows already transformed. `transform_pipeline(transformer, features)`
applies the stored fill values, levels, date parts, centers and scales to new
rows. The input width must match the fitted `input_names`. `names` defaults to
`x1`, `x2`, ...

Step order matters. A typical order is impute, then date, then encode, then
scale. Scaling before encoding fails on categorical columns, encoding before
imputing can turn missing values into a separate `null` category, and imputing
after date expansion cannot fill a calendar column back into a date.

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
impute, date expansion, one-hot encoding and standardization.

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

```bash
pea run examples/use_cases/20_feature_pipeline.pea
```

The example builds a churn table with categorical columns plus missing numeric
values, fits a forest through the default pipeline, reports transformed column
names and importance, and scores new records including an unseen region and a
missing tenure. It also calls the `stats` pipeline directly on a feature
matrix.

## Assumptions and limitations

- Categorical detection is automatic: a column is categorical if any observed
  value is not a number. To force numeric-looking codes through encoding,
  convert them to strings first or encode them before building the matrix.
- One-hot encoding expands width with every level. High-cardinality columns can
  produce very wide matrices; use ordinal encoding or group rare levels first.
- Unseen categories do not raise; they become all-zero one-hot rows or `-1`
  ordinal codes. Monitor this on production data.
- Interpolated imputation is not supported: there is no forward fill, linear
  interpolation or model-based imputation in this layer.
- There is no column subsetting step, target encoding or interaction expansion.
  Use `analysis` helpers or `stats.polynomial_features` before the pipeline
  when you need those.
- Date detection is a heuristic: only the date component is used and an
  eight-digit string that happens to be a valid date is treated as one. Use
  explicit steps without a date step to opt out. See
  [`docs/DATE_FEATURES.md`](DATE_FEATURES.md).
- The fitted transformer stores levels, fills, date parts and scales, not the
  training rows. It is safe to keep alongside the model, but its input column
  order must be preserved.
- `model_pipeline` drops rows with a missing target but keeps rows with missing
  features, relying on the impute step.
