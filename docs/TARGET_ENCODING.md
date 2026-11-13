# Target Encoding

Target encoding, also called mean encoding, replaces each category with the
average target observed for that category. A `store` column with thousands of
stores becomes one numeric column instead of thousands of sparse one-hot
columns. It is a standard trick for high-cardinality categorical data.

PeaLang's implementation is pure Python and dependency-free. The same maths
backs the `target` pipeline step, which fits the category means on training rows
and reapplies them to new data.

Exposed through:

- `stats.*` — global namespace, always available.
- `std.stats.*` — stable standard-library module.
- the `target` step in `stats.fit_pipeline`
- `analysis.model_pipeline`, which passes the training target to the step.

## Quick start

```pea
let seen_stores = [r["store"] for r in rows]
let outcomes = [r["sales"] for r in rows]

let encoder = stats.target_encode(seen_stores, outcomes, 10.0, 1)
print encoder["prior"]
print encoder["levels"]

let values = stats.target_apply(encoder, ["alpha", "zulu"])
print values
```

`stats.target_encode(values, target, smoothing, min_count)` fits an encoder and
returns a plain record:

| Field | Meaning |
|---|---|
| `method` | always `"mean"` |
| `smoothing` | smoothing weight used |
| `min_count` | minimum group size used |
| `prior` | overall target mean |
| `kind` | `"numeric"` or `"binary"` |
| `classes` | two class labels for binary targets, else `[]` |
| `levels` | `{level, count, mean, encoded}` records in sorted order |
| `n` | number of rows used |

`stats.target_apply(encoder, values)` returns one float per value. Unseen
categories and missing values encode to the fitted `prior`.

## Smoothing

Rare categories have noisy means. Smoothing pulls each category towards the
overall mean:

```
encoded = (count * mean + smoothing * prior) / (count + smoothing)
```

- `smoothing = 0` uses the raw category mean.
- Larger values shrink small groups harder; the default is `10.0`.
- A level seen fewer than `min_count` times encodes to the prior. The default
  `min_count` is `1`.

```pea
let raw_encoder = stats.target_encode(seen_stores, outcomes, 0.0, 1)
let shrunk = stats.target_encode(seen_stores, outcomes, 200.0, 1)
print stats.target_apply(raw_encoder, ["alpha"])
print stats.target_apply(shrunk, ["alpha"])
```

The encoder records the level `count`, raw `mean` and smoothed `encoded` value,
so you can inspect exactly what a category became.

## Targets

- Numeric targets are used as-is. This covers regression and numeric
  classification codes.
- Two-class targets are mapped to `0` and `1` in sorted class order. The
  encoded value is then the smoothed proportion of the second class. The
  encoder reports that order in `classes`.
- More than two non-numeric classes raise `ValueError`. Encode multiclass
  targets to numeric columns first, or use one-hot/ordinal encoding.

Target values must be complete: a missing target raises with its row index.
Filter or impute the target before fitting.

## Pipeline step

```pea
let steps = [
    {"op": "impute", "method": "auto"},
    {"op": "target", "columns": ["store"], "smoothing": 10.0},
    {"op": "encode", "method": "onehot"},
    {"op": "scale", "method": "standard"}
]
let fitted = stats.fit_pipeline(steps, features, ["store", "region", "spend"], target)
print fitted["names"]
print fitted["steps"][1]["columns"]
```

The target vector is the fourth argument to `stats.fit_pipeline`. The step
accepts:

| Field | Default | Meaning |
|---|---|---|
| `columns` | auto | names to encode; a string or list |
| `smoothing` | `10.0` | smoothing weight |
| `min_count` | `1` | minimum group size |
| `required` | `true` | raise when no column is encoded |
| `method` | `"mean"` | only mean encoding is supported |

Aliases: `target_encode` for `target`.

With no `columns`, every non-numeric column is encoded. Columns that are
already numeric pass through untouched, so a following `encode` step ignores
them. Naming `columns` explicitly also allows numeric category codes such as
ZIP codes, which are not detected automatically.

The fitted column entries are `{name, encoded, levels}`; unencoded columns keep
`encoded: false` and an empty level list. Output names are unchanged, so a
target-encoded column stays one feature wide.

`required: false` makes the step a no-op when no categorical column is present.
An explicit step raises when it finds nothing, which catches a misspelled column
or an all-numeric feature set.

Step order matters: impute, then target, then encode, then scale. Imputing first
turns missing categories into a real level; scaling last keeps the encoded
values numeric. A target-encoded column is numeric, so `encode` leaves it alone
and `scale` standardizes it.

## Model wrapper

`analysis.model_pipeline` passes the training outcomes to every pipeline step,
so a target step works without extra plumbing:

```pea
let steps = [
    {"op": "target", "columns": ["store"], "smoothing": 10.0},
    {"op": "encode", "method": "onehot"},
    {"op": "scale", "method": "standard"}
]
let model = analysis.model_pipeline(
    rows, "sales", ["store", "region"], steps, "tree", "regression",
    {"max_depth": 5}
)
print model["output_features"]
print analysis.predict_pipeline(model, [{"store": "alpha", "region": "north"}])
```

The default plan does not include a target step. Target encoding leaks target
information unless it is fitted on training data only, so it stays an explicit
choice.

## Persistence

Fitted target steps are JSON-safe and round-trip through the model persistence
layer:

```pea
stats.save_model("model.json", model)
let loaded = stats.load_model("model.json")
print analysis.predict_pipeline(loaded, new_rows)["predicted"]
```

The stored step keeps the prior, smoothing, minimum count and every level's
encoded value, so no training rows are needed at scoring time. See
[`docs/MODEL_PERSISTENCE.md`](MODEL_PERSISTENCE.md).

## Leakage

Category means are computed from the rows being encoded, including each row's
own target. That is fine for a held-out test set, but training-set encodings are
optimistic: a category seen once takes that row's target value exactly.

- Fit the encoder on training data and apply it to validation or test data.
- Prefer `smoothing > 0` and a `min_count` of at least a handful of rows.
- When cross-validating, fit the step inside each fold. PeaLang does not
  cross-fit target encoding automatically.
- For a quick diagnostic, compare training and holdout scores. A large gap
  suggests the encoding, or the model, is memorising categories.

This layer does not add noise to encoded values, which keeps results
deterministic and testable.

## Assumptions and limitations

- Only mean encoding is implemented. There is no median, count, weight-of-
  evidence or per-class multiclass encoding.
- Categories are compared by type and value. `1`, `1.0` and `"1"` are distinct
  levels.
- Missing feature values become a `null` level when they appear during fitting;
  new missing values fall back to the prior if that level was unseen.
- The encoder stores every level. For millions of distinct categories the
  fitted record is large; group rare levels first.
- Binary class order is sorted, not first-seen. Read `classes` when the
  direction of the encoded rate matters.

## Runnable example

- [`examples/use_cases/23_target_encoding.pea`](../examples/use_cases/23_target_encoding.pea)

```bash
pea run examples/use_cases/23_target_encoding.pea
```

The example encodes eight stores with smoothing, shows raw versus heavily
smoothed values, compares a target-encoded model against one-hot encoding,
scores an unseen store, reloads the saved model and reports a binary-target
prior.
