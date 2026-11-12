# Model Persistence

Fitted PeaLang estimators and fitted pipeline transformers are ordinary
records, so they can be written to disk without pickle, joblib or any other
serialization library. The persistence layer wraps them in a small versioned
JSON document, validates the contents, and reads them back ready for scoring.

Everything is exposed through `stats` (and `std.stats`):

- `stats.save_model(path, model)` — write a fitted model or transformer
- `stats.load_model(path)` — read it back
- `stats.export_model(model, compact)` — produce the document as a record
- `stats.import_model(document)` — validate a document from memory
- `stats.model_summary(model)` — describe a fitted model or transformer

There are no third-party dependencies and no executable payloads.

## Document format

```json
{
  "format": "pealang.model",
  "version": 1,
  "kind": "model",
  "payload": {
    "estimator": "random_forest",
    "task": "classification",
    "classes": [0, 1],
    "trees": [...],
    "preprocessor": {"steps": [...], "input_names": ["region", "spend"]}
  }
}
```

`kind` is `"model"` for an estimator and `"pipeline"` for a fitted
transformer. `payload` is the fitted record itself, so a saved file is
inspectable with any text editor and diff-friendly in version control.

The format and version are checked on load. A file with another `format`, a
newer `version`, or a `kind` that does not match its payload raises a
`ValueError` rather than silently producing a broken model.

## Saving and loading

```pea
let model = analysis.model_pipeline(
    rows, "churn", ["region", "plan", "spend"],
    null, "forest", "auto", {"n_estimators": 100, "max_depth": 4}
)

let target = "churn_model.json"
stats.save_model(target, model)
let loaded = stats.load_model(target)

print analysis.predict_pipeline(loaded, new_rows)["predicted"]
```

`save_model(path, model, indent, compact)` creates parent directories and
returns the written path. `indent = 0` writes minified JSON. `load_model(path)`
returns the record unchanged, so it works with every estimator's predict
function and with `stats.transform_pipeline`.

## Compact documents

A fitted `analysis.model_pipeline` record keeps the training predictions and,
for forests, the out-of-bag predictions. These are useful for diagnostics but
not needed for scoring.

```pea
let full = stats.export_model(model)
let small = stats.export_model(model, true)
print len(str(small)) < len(str(full))
```

`compact = true` drops `train_predictions` and `oob_predictions` from the
document. The estimator, trees, classes, importance, metrics and preprocessor
are kept, and predictions are identical.

## In-memory documents

`export_model` and `import_model` are the same machinery without files. Use
them to store a model in a database column, send it over a message bus or keep
it inside another record.

```pea
let document = stats.export_model(model)
let copy = stats.import_model(document)
print stats.model_summary(copy)["estimator"]
```

`import_model` validates the format, version, kind and payload types. It never
executes code from the document.

## Summaries

`model_summary(model)` returns a small record suitable for logs and dashboards.

```pea
let summary = stats.model_summary(model)
print summary["estimator"]
print summary["task"]
print summary["n"]
print summary["metrics"]["train_accuracy"]
print summary["top_features"][0]["feature"]
```

| Field | Model | Pipeline |
|---|---|---|
| `kind` | `"model"` | `"pipeline"` |
| `estimator` | estimator name | — |
| `task` | `classification` or `regression` | — |
| `features` | raw input columns | — |
| `output_features` | transformed columns | — |
| `input_names` | — | raw input columns |
| `names` | — | transformed columns |
| `n_features` | number of raw features | number of output columns |
| `classes` | class labels | — |
| `n` | rows used to fit | rows used to fit |
| `metrics` | training and OOB metrics | — |
| `top_features` | up to five importance entries | — |
| `has_preprocessor` | `true` when fitted by `model_pipeline` | — |
| `steps` | — | step operation names |

`metrics` contains only the values present on the model:
`train_accuracy`, `train_log_loss`, `train_r2`, `train_rmse` and `oob_score`.
A raw `stats.decision_tree` model has none of them.

## What is stored

The document contains everything that scoring needs:

- the estimator name, task, hyperparameters and random seed
- the tree, forest or boosting stage structure with split features,
  thresholds, leaf values and class probabilities
- class labels and feature importances
- the fitted preprocessor: fill values, category levels, centers and scales
- training diagnostics and importance tables until a compact save drops them

It does not store the training rows, the original file paths or any Python
objects that are not plain records, lists, strings, numbers, booleans or
`null`.

## Validation

Persistence rejects values that would not survive a JSON round trip:

- top-level values that are not records
- records that were not produced by a stats estimator or pipeline
- non-finite numbers such as `inf` and `nan`
- record keys that are not strings
- arbitrary Python objects such as file handles or dataframes

Loading also rejects malformed JSON, unknown formats and versions, missing
payloads and mismatched kinds. Errors are `ValueError` with a short message so
they read well from PeaLang.

## Runnable example

- [`examples/use_cases/21_model_persistence.pea`](../examples/use_cases/21_model_persistence.pea)

```bash
pea run examples/use_cases/21_model_persistence.pea
```

The example fits a forest through the default pipeline, writes
`churn_model.json`, reloads it, prints a summary and shows that the reloaded
model produces exactly the same predictions. It also compares a full and a
compact document.

## Assumptions and limitations

- The file format is plain JSON by design. Very large forests produce large
  files; use `compact` and a smaller `n_estimators` when size matters.
- There is no checksum, signature or encryption. Use file permissions or a
  separate signing step when models cross a trust boundary.
- The document is not a package format. Feature names and column order must
  match between training and scoring; the preprocessor raises when the width
  differs.
- Forward compatibility is explicit: a newer `version` is rejected rather than
  guessed. Re-save models after upgrading if the format changes.
- Only `stats` estimators and pipeline transformers are supported. The older
  object-based `ml` stack keeps its own separate model files.
